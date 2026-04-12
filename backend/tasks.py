import asyncio
import json
import os
from typing import Any, Dict

from redis import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

import effort_engine
import github_fetcher
import jira_fetcher
from celery_app import celery_app
from jira_fetcher import TicketTooVague
from models import CommitScore, engine


REDIS_URL = os.getenv("REDIS_URL", "").strip()
if not REDIS_URL:
    raise RuntimeError("REDIS_URL environment variable is required")

_redis = Redis.from_url(REDIS_URL, decode_responses=True)
_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def _upsert_commit_score(data: Dict[str, Any]) -> None:
    async with _session_factory() as session:
        existing = await session.scalar(select(CommitScore).where(CommitScore.commit_sha == data["commit_sha"]))

        if existing is None:
            session.add(CommitScore(**data))
        else:
            for key, value in data.items():
                setattr(existing, key, value)

        await session.commit()


@celery_app.task(bind=True, autoretry_for=(Exception,), max_retries=5, retry_backoff=True)
def process_commit(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    org_id = str(payload.get("org_id", "")).strip()
    developer = str(payload.get("developer", "")).strip()
    branch = str(payload.get("branch", "")).strip()
    commit_sha = str(payload.get("commit_sha", "")).strip()
    repo = str(payload.get("repo", "")).strip()
    ticket_id = str(payload.get("ticket_id", "")).strip()

    if not org_id or not developer or not commit_sha or not repo:
        raise ValueError("payload must include org_id, developer, commit_sha, and repo")

    diff_result = github_fetcher.get_diff(repo, commit_sha)
    diff_text = str(diff_result.get("diff_text", "") or "")

    try:
        ticket = jira_fetcher.get_ticket(ticket_id)
    except TicketTooVague as exc:
        vague_message = f"unscored: vague ticket ({str(exc)})"

        asyncio.run(
            _upsert_commit_score(
                {
                    "org_id": org_id,
                    "developer": developer,
                    "commit_sha": commit_sha,
                    "branch": branch or None,
                    "ticket_id": ticket_id or None,
                    "score": None,
                    "relevance": None,
                    "impact": None,
                    "complexity": None,
                    "glue_work": None,
                    "confidence": "low",
                    "plain_english": vague_message,
                    "diff_translation": diff_text,
                }
            )
        )
        return {
            "status": "unscored: vague ticket",
            "developer": developer,
        }

    jira_context = str(ticket.get("context", "") or "")

    commit_metadata = {
        "files_changed": int(diff_result.get("files_changed", 0) or 0),
        "changed_files": diff_result.get("changed_files", []),
        "core_files": payload.get("core_files", []),
        "old_coverage": float(payload.get("old_coverage", 0.0) or 0.0),
        "new_coverage": float(payload.get("new_coverage", 0.0) or 0.0),
        "commit_date": payload.get("commit_date"),
        "ticket_in_progress_date": payload.get("ticket_in_progress_date"),
        "additions": int(diff_result.get("lines_added", 0) or 0),
        "deletions": int(diff_result.get("lines_deleted", 0) or 0),
        "week_start": payload.get("week_start"),
    }

    score_result = effort_engine.score(diff_text, jira_context, developer, commit_metadata)
    score_value = float(score_result.get("score", 0.0) or 0.0)
    breakdown = score_result.get("breakdown", {}) if isinstance(score_result.get("breakdown", {}), dict) else {}

    asyncio.run(
        _upsert_commit_score(
            {
                "org_id": org_id,
                "developer": developer,
                "commit_sha": commit_sha,
                "branch": branch or None,
                "ticket_id": ticket_id or None,
                "score": score_value,
                "relevance": float(breakdown.get("relevance", 0.0) or 0.0),
                "impact": float(breakdown.get("impact", 0.0) or 0.0),
                "complexity": float(breakdown.get("complexity", 0.0) or 0.0),
                "glue_work": float(breakdown.get("glue_work", 0.0) or 0.0),
                "confidence": str(score_result.get("confidence", "uncertain") or "uncertain"),
                "plain_english": str(score_result.get("plain_english_explanation", "") or ""),
                "diff_translation": diff_text,
            }
        )
    )

    score_payload = {
        "org_id": org_id,
        "developer": developer,
        "commit_sha": commit_sha,
        "score": score_value,
        "status": "scored",
        "breakdown": breakdown,
        "confidence": score_result.get("confidence", "uncertain"),
    }

    _redis.setex(f"score:{org_id}:{developer}:latest", 300, json.dumps(score_payload))
    _redis.publish(f"scores:{org_id}", json.dumps(score_payload))

    return {
        "status": "scored",
        "score": score_value,
        "developer": developer,
    }
