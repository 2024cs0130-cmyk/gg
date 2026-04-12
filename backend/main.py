# pip install python-jose[cryptography] passlib[bcrypt] reportlab python-multipart

import hashlib
import hmac
import json
import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from jose.utils import base64url_decode, base64url_encode

# Load environment variables before importing modules that use them
load_dotenv()

from auth import get_current_user  # noqa: F401
from auth_models import Base as AuthBase
from auth_routes import router as auth_router
from models import engine


GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "").strip()
if not GITHUB_WEBHOOK_SECRET:
    raise RuntimeError("GITHUB_WEBHOOK_SECRET environment variable is required")

TICKET_PATTERN = re.compile(r"[A-Z]+-\d+")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount websocket routes for real-time org score streaming.
from websocket import router as websocket_router

app.include_router(websocket_router)
app.include_router(auth_router)


@app.on_event("startup")
async def startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(AuthBase.metadata.create_all)
    print("All database tables created")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}


def _normalize_secret(secret: str) -> bytes:
    # Use python-jose utilities to normalize secret bytes consistently.
    return bytes(base64url_decode(base64url_encode(secret.encode("utf-8"))))


def _validate_signature(signature_header: str, raw_body: bytes) -> None:
    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing or invalid X-Hub-Signature-256 header")

    digest = hmac.new(_normalize_secret(GITHUB_WEBHOOK_SECRET), raw_body, hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"

    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


def _extract_branch_name(ref: str) -> str:
    if ref.startswith("refs/heads/"):
        return ref[len("refs/heads/") :]
    return ref


def _extract_ticket_id(branch_name: str, commit_messages: List[str]) -> Optional[str]:
    branch_match = TICKET_PATTERN.search(branch_name or "")
    if branch_match:
        return branch_match.group(0)

    for message in commit_messages:
        msg_match = TICKET_PATTERN.search(message or "")
        if msg_match:
            return msg_match.group(0)

    return None


def _extract_modified_files(commits: List[Dict[str, Any]]) -> List[str]:
    files = set()
    for commit in commits:
        for key in ("modified", "added", "removed"):
            for file_path in commit.get(key, []) or []:
                if file_path:
                    files.add(str(file_path))
    return sorted(files)


@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(default="", alias="X-Hub-Signature-256"),
    x_github_event: str = Header(default="")
) -> Dict[str, str]:

    if x_github_event == "ping":
        return {"message": "pong"}

    raw_body = await request.body()
    _validate_signature(x_hub_signature_256, raw_body)
    try:
        body = json.loads(raw_body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    ref = str(body.get("ref", "") or "")
    branch = _extract_branch_name(ref)

    head_commit = body.get("head_commit") or {}
    commits = body.get("commits") or []

    commit_sha = str(head_commit.get("id") or body.get("after") or "").strip()
    pusher = body.get("pusher") or {}
    developer = str(pusher.get("name") or pusher.get("username") or pusher.get("email") or "").strip()

    commit_messages = [str(c.get("message", "") or "") for c in commits]
    if head_commit.get("message"):
        commit_messages.append(str(head_commit.get("message")))

    ticket_id = _extract_ticket_id(branch, commit_messages)
    modified_files = _extract_modified_files(commits)

    repository = body.get("repository") or {}
    owner = repository.get("owner") or {}
    org_id = str(owner.get("login") or owner.get("name") or "").strip()
    repo = str(repository.get("full_name") or "").strip()

    task_payload: Dict[str, Any] = {
        "org_id": org_id,
        "developer": developer,
        "branch": branch,
        "commit_sha": commit_sha,
        "repo": repo,
        "ticket_id": ticket_id,
        "modified_files": modified_files,
    }

    # Import lazily to keep startup and request-path overhead minimal.
    from tasks import process_commit

    process_commit.delay(task_payload)

    return {"status": "queued"}
