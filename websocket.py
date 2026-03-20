import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from models import CommitScore, engine


REDIS_URL = os.getenv("REDIS_URL", "").strip()
if not REDIS_URL:
    raise RuntimeError("REDIS_URL environment variable is required")

router = APIRouter()

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
session_factory = async_sessionmaker(engine, expire_on_commit=False)

active_connections: Dict[str, Set[WebSocket]] = {}
org_listener_tasks: Dict[str, asyncio.Task] = {}
connection_lock = asyncio.Lock()


def _format_message(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "developer": str(data.get("developer", "") or ""),
        "score": float(data.get("score", 0.0) or 0.0),
        "confidence": str(data.get("confidence", "uncertain") or "uncertain"),
        "explanation": str(data.get("explanation", "") or ""),
        "breakdown": data.get("breakdown", {}) if isinstance(data.get("breakdown"), dict) else {},
        "timestamp": str(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
    }


async def _broadcast_to_org(org_id: str, message: Dict[str, Any]) -> None:
    formatted = _format_message(message)

    async with connection_lock:
        sockets = list(active_connections.get(org_id, set()))

    if not sockets:
        return

    stale_connections: List[WebSocket] = []
    for websocket in sockets:
        try:
            await websocket.send_json(formatted)
        except Exception:
            stale_connections.append(websocket)

    if stale_connections:
        async with connection_lock:
            current = active_connections.get(org_id, set())
            for stale in stale_connections:
                current.discard(stale)
            if not current:
                active_connections.pop(org_id, None)


async def _fetch_last_scores(org_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    async with session_factory() as session:
        rows = await session.scalars(
            select(CommitScore)
            .where(CommitScore.org_id == org_id)
            .order_by(desc(CommitScore.created_at))
            .limit(limit)
        )
        records = list(rows)

    records.reverse()
    return [
        _format_message(
            {
                "developer": record.developer,
                "score": record.score or 0.0,
                "confidence": record.confidence or "uncertain",
                "explanation": record.plain_english or "",
                "breakdown": {
                    "relevance": record.relevance,
                    "impact": record.impact,
                    "complexity": record.complexity,
                    "glue_work": record.glue_work,
                },
                "timestamp": record.created_at.isoformat() if record.created_at else datetime.now(timezone.utc).isoformat(),
            }
        )
        for record in records
    ]


async def _pubsub_listener(org_id: str) -> None:
    channel = f"scores:{org_id}"
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is None:
                await asyncio.sleep(0.05)
                continue

            payload = message.get("data")
            if not payload:
                continue

            try:
                parsed = json.loads(payload)
            except (TypeError, ValueError):
                continue

            outbound = {
                "developer": parsed.get("developer", ""),
                "score": parsed.get("score", 0.0),
                "confidence": parsed.get("confidence", "uncertain"),
                "explanation": parsed.get("plain_english_explanation", parsed.get("explanation", "")),
                "breakdown": parsed.get("breakdown", {}),
                "timestamp": parsed.get("timestamp", datetime.now(timezone.utc).isoformat()),
            }
            await _broadcast_to_org(org_id, outbound)

            async with connection_lock:
                has_connections = bool(active_connections.get(org_id))
            if not has_connections:
                break
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()


async def _ensure_listener(org_id: str) -> None:
    async with connection_lock:
        task = org_listener_tasks.get(org_id)
        if task and not task.done():
            return
        org_listener_tasks[org_id] = asyncio.create_task(_pubsub_listener(org_id))


async def _heartbeat(websocket: WebSocket) -> None:
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json(
                {
                    "type": "ping",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
    except Exception:
        return


async def _remove_connection(org_id: str, websocket: WebSocket) -> None:
    async with connection_lock:
        org_sockets = active_connections.get(org_id, set())
        org_sockets.discard(websocket)

        if not org_sockets:
            active_connections.pop(org_id, None)
            task = org_listener_tasks.pop(org_id, None)
            if task and not task.done():
                task.cancel()


@router.websocket("/ws/{org_id}")
async def org_scores_websocket(websocket: WebSocket, org_id: str) -> None:
    await websocket.accept()

    async with connection_lock:
        org_sockets = active_connections.setdefault(org_id, set())
        org_sockets.add(websocket)

    await _ensure_listener(org_id)

    history = await _fetch_last_scores(org_id)
    for item in history:
        await websocket.send_json(item)

    heartbeat_task = asyncio.create_task(_heartbeat(websocket))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        heartbeat_task.cancel()
        await _remove_connection(org_id, websocket)
