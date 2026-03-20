import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Coroutine, Optional, TypeVar

from cryptography.fernet import Fernet, InvalidToken
from redis import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from models import APIKey, engine


_ALLOWED_SERVICES = {"github", "jira"}
_CACHE_TTL_SECONDS = 300
T = TypeVar("T")
_MASTER_KEY = os.getenv("MASTER_ENCRYPTION_KEY", "").strip()
REDIS_URL = os.getenv("REDIS_URL", "").strip()

if not _MASTER_KEY:
    raise RuntimeError("MASTER_ENCRYPTION_KEY environment variable is required")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL environment variable is required")

try:
    _fernet = Fernet(_MASTER_KEY.encode("utf-8"))
except Exception as exc:
    raise RuntimeError("MASTER_ENCRYPTION_KEY must be a valid Fernet key") from exc

_redis = Redis.from_url(REDIS_URL, decode_responses=True)
_session_factory = async_sessionmaker(engine, expire_on_commit=False)


def _validate_service(service: str) -> str:
    normalized = str(service or "").strip().lower()
    if normalized not in _ALLOWED_SERVICES:
        raise ValueError("service must be 'github' or 'jira'")
    return normalized


def _cache_key(org_id: str, service: str) -> str:
    return f"api_key:{org_id}:{service}"


def _run_coro_sync(coro: Coroutine[Any, Any, T]) -> T:
    """Run async DB operations from both sync and async call sites."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(lambda: asyncio.run(coro)).result()


def encrypt_key(raw_token: str) -> str:
    token_buffer = bytearray((raw_token or "").encode("utf-8"))
    if not token_buffer:
        raise ValueError("raw_token must not be empty")

    try:
        encrypted = _fernet.encrypt(bytes(token_buffer)).decode("utf-8")
        return encrypted
    finally:
        for i in range(len(token_buffer)):
            token_buffer[i] = 0


def decrypt_key(encrypted_token: str) -> str:
    if not encrypted_token:
        raise ValueError("encrypted_token must not be empty")

    try:
        decrypted = _fernet.decrypt(encrypted_token.encode("utf-8"))
    except InvalidToken as exc:
        raise ValueError("encrypted_token is invalid or cannot be decrypted") from exc

    return decrypted.decode("utf-8")


async def _upsert_api_key(org_id: str, service: str, encrypted_token: str) -> None:
    async with _session_factory() as session:
        existing = await session.scalar(
            select(APIKey).where(APIKey.org_id == org_id, APIKey.service == service)
        )

        if existing is None:
            session.add(
                APIKey(
                    org_id=org_id,
                    service=service,
                    encrypted_token=encrypted_token,
                )
            )
        else:
            existing.encrypted_token = encrypted_token

        await session.commit()


async def _get_encrypted_api_key(org_id: str, service: str) -> Optional[str]:
    async with _session_factory() as session:
        record = await session.scalar(
            select(APIKey).where(APIKey.org_id == org_id, APIKey.service == service)
        )
        if record is None:
            return None
        return str(record.encrypted_token)


def store_api_key(org_id: str, service: str, raw_token: str) -> None:
    service_normalized = _validate_service(service)
    org_id = str(org_id or "").strip()
    if not org_id:
        raise ValueError("org_id must not be empty")

    encrypted_token = encrypt_key(raw_token)

    # Best-effort cleanup for the provided raw token reference.
    raw_token = ""
    del raw_token

    _run_coro_sync(_upsert_api_key(org_id, service_normalized, encrypted_token))
    _redis.delete(_cache_key(org_id, service_normalized))


def get_api_key(org_id: str, service: str) -> str:
    service_normalized = _validate_service(service)
    org_id = str(org_id or "").strip()
    if not org_id:
        raise ValueError("org_id must not be empty")

    cached = _redis.get(_cache_key(org_id, service_normalized))
    if cached:
        return cached

    encrypted_token = _run_coro_sync(_get_encrypted_api_key(org_id, service_normalized))
    if not encrypted_token:
        raise KeyError(f"No API key found for org_id={org_id} service={service_normalized}")

    raw_token = decrypt_key(encrypted_token)
    _redis.setex(_cache_key(org_id, service_normalized), _CACHE_TTL_SECONDS, raw_token)
    return raw_token


def rotate_key(org_id: str, service: str, new_raw_token: str) -> None:
    store_api_key(org_id=org_id, service=service, raw_token=new_raw_token)
