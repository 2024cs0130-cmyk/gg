import hashlib
import hmac
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator, Dict

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from auth_models import User
from models import engine


load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256").strip() or "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = 7

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is required")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
_session_factory = async_sessionmaker(engine, expire_on_commit=False)


def hash_password(plain: str) -> str:
    """Hash a password using bcrypt. For passwords, we use bcrypt."""
    try:
        return pwd_context.hash(plain)
    except Exception:
        import bcrypt

        hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")


def hash_token(token: str) -> str:
    """Hash a JWT token using SHA256 (handles length > 72 bytes)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token_hash(raw_token: str, stored_hash: str) -> bool:
    """Verify a JWT token against its stored hash using constant-time comparison."""
    computed_hash = hash_token(raw_token)
    return hmac.compare_digest(computed_hash, stored_hash)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        import bcrypt

        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False


def _build_token_payload(data: Dict[str, Any], expires_delta: timedelta) -> Dict[str, Any]:
    sub = data.get("sub")
    role = data.get("role")
    org_id = data.get("org_id")
    display_name = data.get("display_name")

    if not sub or not role or not org_id:
        raise ValueError("Token data must include sub, role, and org_id")

    expire_at = datetime.now(timezone.utc) + expires_delta

    return {
        "sub": str(sub),
        "role": str(role),
        "org_id": str(org_id),
        "display_name": str(display_name or ""),
        "exp": expire_at,
    }


def create_access_token(data: Dict[str, Any]) -> str:
    payload = _build_token_payload(data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    payload = _build_token_payload(data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise credentials_error from exc

    required_claims = ("sub", "role", "org_id", "display_name", "exp")
    if any(claim not in payload for claim in required_claims):
        raise credentials_error

    return payload


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = verify_token(token)
    user_id_raw = payload.get("sub")

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user_id = uuid.UUID(str(user_id_raw))
    except (TypeError, ValueError) as exc:
        raise credentials_error from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not bool(user.is_active):
        raise credentials_error

    return user


async def require_developer(user: User = Depends(get_current_user)) -> User:
    if user.role not in {"developer", "manager", "ceo"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="developer access required")
    return user


async def require_manager(user: User = Depends(get_current_user)) -> User:
    if user.role not in {"manager", "ceo"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="manager access required")
    return user


async def require_ceo(user: User = Depends(get_current_user)) -> User:
    if user.role != "ceo":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CEO access required")
    return user
