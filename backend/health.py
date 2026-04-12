import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from redis import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

# Load environment variables early
load_dotenv()

from celery_app import DEAD_LETTER_QUEUE, celery_app
from models import CommitScore, engine
from tasks import process_commit


logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "").strip()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()
MIN_WORKERS = int(os.getenv("MIN_WORKERS", "4"))

if not REDIS_URL:
    raise RuntimeError("REDIS_URL environment variable is required")

_redis = Redis.from_url(REDIS_URL, decode_responses=True)
_session_factory = async_sessionmaker(engine, expire_on_commit=False)


def _send_slack_alert(message: str) -> None:
    if not SLACK_WEBHOOK_URL:
        return

    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=2.5)
    except Exception:
        logger.exception("Failed sending Slack alert")


@celery_app.task(name="health.worker_health_check")
def worker_health_check() -> Dict[str, Any]:
    responses = celery_app.control.ping(timeout=1.0) or []
    worker_count = len(responses)

    _redis.set("health:worker_count", str(worker_count))

    if worker_count < MIN_WORKERS:
        msg = f"Worker count below minimum: active={worker_count}, min_required={MIN_WORKERS}"
        logger.warning(msg)
        _send_slack_alert(f":warning: {msg}")

    return {"worker_count": worker_count, "min_workers": MIN_WORKERS}


@celery_app.task(name="health.queue_depth_monitor")
def queue_depth_monitor() -> Dict[str, Any]:
    # Celery's default Redis list queue key is usually the queue name itself.
    depth = int(_redis.llen("celery"))
    _redis.set("health:queue_depth", str(depth))

    if depth > 5000:
        msg = f"CRITICAL queue depth detected: depth={depth}"
        logger.error(msg)
        _send_slack_alert(f":rotating_light: {msg}")
    elif depth > 1000:
        msg = f"HIGH QUEUE DEPTH detected: depth={depth}"
        logger.warning(msg)
        _send_slack_alert(f":warning: {msg}")

    return {"queue_depth": depth}


def _extract_payload_from_dead_letter(entry: str) -> Optional[Dict[str, Any]]:
    try:
        parsed = json.loads(entry)
    except (TypeError, ValueError):
        return None

    if isinstance(parsed, dict) and isinstance(parsed.get("payload"), dict):
        return parsed["payload"]

    failed_task = parsed.get("failed_task") if isinstance(parsed, dict) else None
    if isinstance(failed_task, dict):
        args = failed_task.get("args") or []
        kwargs = failed_task.get("kwargs") or {}

        if args and isinstance(args[0], dict):
            return args[0]

        payload = kwargs.get("payload")
        if isinstance(payload, dict):
            return payload

    return None


@celery_app.task(name="health.drain_dead_letter")
def drain_dead_letter() -> Dict[str, Any]:
    entries: List[str] = _redis.lrange(DEAD_LETTER_QUEUE, 0, -1)
    retried_count = 0

    for entry in entries:
        payload = _extract_payload_from_dead_letter(entry)
        if not payload:
            continue
        process_commit.apply_async(args=[payload])
        retried_count += 1

    if entries:
        _redis.delete(DEAD_LETTER_QUEUE)

    logger.info("Retried tasks from dead letter queue: %s", retried_count)
    return {"retried_tasks": retried_count, "dead_letter_entries": len(entries)}


async def _pipeline_status() -> Dict[str, Any]:
    async with _session_factory() as session:
        total_commits = await session.scalar(select(func.count(CommitScore.id)))

        last_score = await session.scalar(
            select(func.max(CommitScore.created_at)).where(CommitScore.score.isnot(None))
        )

    return {
        "total_commits": int(total_commits or 0),
        "last_score": last_score,
    }


@celery_app.task(name="health.stale_pipeline_detector")
def stale_pipeline_detector() -> Dict[str, Any]:
    status = asyncio.run(_pipeline_status())
    total_commits = int(status["total_commits"])
    last_score = status.get("last_score")

    last_score_iso = "none"
    if last_score is not None:
        if last_score.tzinfo is None:
            last_score = last_score.replace(tzinfo=timezone.utc)
        last_score_iso = last_score.isoformat()

    _redis.set("health:last_score_time", last_score_iso)

    if total_commits <= 0:
        return {"stale": False, "reason": "no commits"}

    now_utc = datetime.now(timezone.utc)
    stale_cutoff = now_utc - timedelta(minutes=30)

    is_stale = last_score is None or last_score < stale_cutoff
    if is_stale:
        msg = (
            "Pipeline appears stale: commits exist but no score in the last 30 minutes. "
            f"last_score={last_score_iso}, commits={total_commits}"
        )
        logger.warning(msg)
        _send_slack_alert(f":warning: {msg}")

    return {
        "stale": is_stale,
        "total_commits": total_commits,
        "last_score_time": last_score_iso,
    }


# Register periodic schedules when this module is imported.
celery_app.conf.beat_schedule.update(
    {
        "worker-health-check-every-60s": {
            "task": "health.worker_health_check",
            "schedule": 60.0,
        },
        "queue-depth-monitor-every-30s": {
            "task": "health.queue_depth_monitor",
            "schedule": 30.0,
        },
        "drain-dead-letter-every-hour": {
            "task": "health.drain_dead_letter",
            "schedule": 3600.0,
        },
        "stale-pipeline-detector-every-15-min": {
            "task": "health.stale_pipeline_detector",
            "schedule": 900.0,
        },
    }
)
