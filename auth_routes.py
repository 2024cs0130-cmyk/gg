import os
import uuid
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_db,
    hash_password,
    hash_token,
    require_ceo,
    require_developer,
    require_manager,
    verify_password,
    verify_token,
    verify_token_hash,
)
from auth_models import Alert, CommitContextNote, RefreshToken, User, WeeklySnapshot
from models import APIKey, CommitScore, Developer, Organisation


load_dotenv()

router = APIRouter()

_ALLOWED_ROLES = {"developer", "manager", "ceo"}
_COMMON_DOMAINS = ["auth", "payments", "mobile", "ml", "devops", "frontend", "database"]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"email": "user@example.com"}})
    
    email: str  # Use plain str to allow .test domains in development
    password: str = Field(min_length=6)
    display_name: Optional[str] = None
    role: str
    org_id: str
    github_username: Optional[str] = None


class LoginRequest(BaseModel):
    email: str  # Use plain str to allow .test domains in development
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ContextNoteRequest(BaseModel):
    context_note: str = Field(min_length=1)


class SpecialtyRequest(BaseModel):
    specialty_text: str = Field(min_length=1)


class AssignTicketRequest(BaseModel):
    ticket_id: str = Field(min_length=1)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid {field_name}") from exc


def _score_breakdown(score: CommitScore) -> Dict[str, Optional[float]]:
    return {
        "relevance": score.relevance,
        "impact": score.impact,
        "complexity": score.complexity,
        "glue_work": score.glue_work,
    }


def _week_start(today: Optional[date] = None) -> date:
    today = today or datetime.now(timezone.utc).date()
    return today - timedelta(days=today.weekday())


def _tokenize(text: str) -> List[str]:
    return [t.strip().lower() for t in text.replace("\n", " ").split() if t.strip()]


def _extract_domain_signals(texts: List[str]) -> List[str]:
    joined = " ".join(texts).lower()
    counts: Counter[str] = Counter()
    for domain in _COMMON_DOMAINS:
        if domain in joined:
            counts[domain] += joined.count(domain)
    return [domain for domain, _ in counts.most_common(5)]


def _streak_above(scores_desc: List[CommitScore], threshold: float) -> int:
    streak = 0
    for row in scores_desc:
        if row.score is None:
            continue
        if float(row.score) > threshold:
            streak += 1
        else:
            break
    return streak


def _refresh_expiry() -> datetime:
    return _utc_now() + timedelta(days=7)


async def _find_active_refresh_token_record(
    db: AsyncSession,
    user_id: uuid.UUID,
    raw_refresh_token: str,
) -> Optional[RefreshToken]:
    rows = await db.scalars(
        select(RefreshToken).where(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked.is_(False),
                RefreshToken.expires_at > _utc_now(),
            )
        )
    )

    for token_row in rows.all():
        if verify_token_hash(raw_refresh_token, token_row.token_hash):
            return token_row
    return None


async def _org_github_repo(db: AsyncSession, org_id: uuid.UUID) -> Optional[str]:
    org = await db.scalar(select(Organisation).where(Organisation.id == org_id))
    if org and org.github_repo:
        return str(org.github_repo)
    return None


@router.post("/auth/register")
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    role = payload.role.strip().lower()
    if role not in _ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="invalid role")

    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="email already exists")

    org_uuid = _to_uuid(payload.org_id, "org_id")
    user = User(
        org_id=org_uuid,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=role,
        display_name=(payload.display_name or "").strip() or None,
        github_username=(payload.github_username or "").strip() or None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role,
        "display_name": user.display_name,
    }


@router.post("/auth/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, str(user.hashed_password)):
        raise HTTPException(status_code=401, detail="wrong credentials")

    if not bool(user.is_active):
        raise HTTPException(status_code=401, detail="wrong credentials")

    claims = {
        "sub": str(user.id),
        "role": str(user.role),
        "org_id": str(user.org_id),
        "display_name": str(user.display_name or ""),
    }

    access_token = create_access_token(claims)
    refresh_token = create_refresh_token(claims)

    refresh_row = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=_refresh_expiry(),
    )
    db.add(refresh_row)

    user.last_login = _utc_now()
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role,
        "org_id": str(user.org_id),
        "display_name": user.display_name,
    }


@router.post("/auth/refresh")
async def refresh_tokens(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    token_payload = verify_token(payload.refresh_token)
    user_id = _to_uuid(str(token_payload.get("sub", "")), "token sub")

    token_row = await _find_active_refresh_token_record(db, user_id, payload.refresh_token)
    if token_row is None:
        raise HTTPException(status_code=401, detail="invalid refresh token")

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None or not bool(user.is_active):
        raise HTTPException(status_code=401, detail="invalid refresh token")

    claims = {
        "sub": str(user.id),
        "role": str(user.role),
        "org_id": str(user.org_id),
        "display_name": str(user.display_name or ""),
    }
    new_access = create_access_token(claims)
    return {"access_token": new_access, "token_type": "bearer"}


@router.post("/auth/logout")
async def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    token_row = await _find_active_refresh_token_record(db, current_user.id, payload.refresh_token)
    if token_row is None:
        raise HTTPException(status_code=401, detail="invalid refresh token")

    token_row.is_revoked = True
    await db.commit()
    return {"message": "logged out"}


@router.get("/auth/me")
async def auth_me(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "org_id": str(current_user.org_id),
        "display_name": current_user.display_name,
        "github_username": current_user.github_username,
    }


@router.get("/developer/me/scores")
async def developer_my_scores(
    current_user: User = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    username = (current_user.github_username or "").strip()
    if not username:
        return []

    rows = await db.scalars(
        select(CommitScore)
        .where(CommitScore.developer == username)
        .order_by(desc(CommitScore.created_at))
        .limit(30)
    )

    result: List[Dict[str, Any]] = []
    for row in rows.all():
        result.append(
            {
                "commit_sha": row.commit_sha,
                "score": row.score,
                "confidence": row.confidence,
                "breakdown": _score_breakdown(row),
                "plain_english": row.plain_english,
                "created_at": row.created_at,
                "developer_seen": bool(row.developer_seen),
            }
        )
    return result


@router.patch("/developer/me/scores/{commit_sha}/seen")
async def developer_ack_score(
    commit_sha: str,
    current_user: User = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    username = (current_user.github_username or "").strip()
    row = await db.scalar(
        select(CommitScore).where(
            and_(CommitScore.commit_sha == commit_sha, CommitScore.developer == username)
        )
    )
    if row is None:
        raise HTTPException(status_code=404, detail="commit score not found")

    row.developer_seen = True
    row.developer_seen_at = _utc_now()
    await db.commit()
    return {"message": "score acknowledged"}


@router.post("/developer/me/scores/{commit_sha}/context")
async def developer_save_context(
    commit_sha: str,
    payload: ContextNoteRequest,
    current_user: User = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    note = CommitContextNote(
        commit_sha=commit_sha,
        developer_id=current_user.id,
        context_note=payload.context_note.strip(),
    )
    db.add(note)
    await db.commit()
    return {"message": "context saved"}


@router.get("/developer/me/achievements")
async def developer_achievements(
    current_user: User = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    username = (current_user.github_username or "").strip()
    if not username:
        return {"personal_best_score": None, "streak": 0, "win_cards_this_week": 0}

    rows = await db.scalars(
        select(CommitScore)
        .where(and_(CommitScore.developer == username, CommitScore.score.is_not(None)))
        .order_by(desc(CommitScore.created_at))
        .limit(300)
    )
    scores = rows.all()
    if not scores:
        return {"personal_best_score": None, "streak": 0, "win_cards_this_week": 0}

    numeric_scores = [float(r.score) for r in scores if r.score is not None]
    personal_avg = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0.0
    win_threshold = personal_avg * 1.15

    ws = _week_start()
    week_start_dt = datetime.combine(ws, datetime.min.time(), tzinfo=timezone.utc)

    win_cards = sum(
        1
        for r in scores
        if r.score is not None
        and float(r.score) >= win_threshold
        and r.created_at is not None
        and (r.created_at if r.created_at.tzinfo else r.created_at.replace(tzinfo=timezone.utc)) >= week_start_dt
    )

    return {
        "personal_best_score": max(numeric_scores) if numeric_scores else None,
        "streak": _streak_above(scores, 70.0),
        "win_cards_this_week": win_cards,
    }


@router.get("/developer/me/profile")
async def developer_profile(
    current_user: User = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    username = (current_user.github_username or "").strip()
    if not username:
        return {
            "coding_dna": [],
            "avg_score_last_30_days": None,
            "total_commits": 0,
            "glue_work_score": None,
        }

    cutoff = _utc_now() - timedelta(days=30)
    rows = await db.scalars(
        select(CommitScore)
        .where(and_(CommitScore.developer == username, CommitScore.created_at >= cutoff))
        .order_by(desc(CommitScore.created_at))
        .limit(200)
    )
    commits = rows.all()

    score_values = [float(r.score) for r in commits if r.score is not None]
    glue_values = [float(r.glue_work) for r in commits if r.glue_work is not None]

    dev_row = await db.scalar(select(Developer).where(Developer.username == username))
    source_texts = [r.plain_english or "" for r in commits] + [r.diff_translation or "" for r in commits]
    if dev_row and dev_row.specialties:
        source_texts.append(str(dev_row.specialties))

    return {
        "coding_dna": _extract_domain_signals(source_texts),
        "avg_score_last_30_days": (sum(score_values) / len(score_values)) if score_values else None,
        "total_commits": len(commits),
        "glue_work_score": (sum(glue_values) / len(glue_values)) if glue_values else None,
    }


@router.get("/manager/team/scores")
async def manager_team_scores(
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    org_id = str(current_user.org_id)
    visibility_cutoff = _utc_now() - timedelta(hours=2)

    developers = await db.scalars(select(Developer).where(Developer.org_id == org_id))
    result: List[Dict[str, Any]] = []
    for dev in developers.all():
        latest = await db.scalar(
            select(CommitScore)
            .where(CommitScore.developer == dev.username)
            .order_by(desc(CommitScore.created_at))
            .limit(1)
        )

        if latest is None:
            continue

        visible = bool(latest.developer_seen) or (
            latest.created_at is not None
            and (latest.created_at if latest.created_at.tzinfo else latest.created_at.replace(tzinfo=timezone.utc))
            <= visibility_cutoff
        )
        if not visible:
            continue

        result.append(
            {
                "developer": dev.username,
                "display_name": dev.display_name,
                "latest_score": latest.score,
                "commit_sha": latest.commit_sha,
                "created_at": latest.created_at,
                "burnout_risk": dev.burnout_risk,
                "burnout_risk_flag": (dev.burnout_risk or "").lower() in {"high", "medium"},
            }
        )

    return result


@router.get("/manager/alerts")
async def manager_alerts(
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    org_id = str(current_user.org_id)
    alerts = await db.scalars(
        select(Alert)
        .where(and_(Alert.org_id == org_id, Alert.is_dismissed.is_(False)))
        .order_by(desc(Alert.created_at))
    )

    return [
        {
            "id": str(a.id),
            "alert_type": a.alert_type,
            "developer_username": a.developer_username,
            "message": a.message,
            "severity": a.severity,
            "created_at": a.created_at,
        }
        for a in alerts.all()
    ]


@router.patch("/manager/alerts/{alert_id}/dismiss")
async def manager_dismiss_alert(
    alert_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    org_id = str(current_user.org_id)
    alert_uuid = _to_uuid(alert_id, "alert_id")

    alert = await db.scalar(select(Alert).where(and_(Alert.id == alert_uuid, Alert.org_id == org_id)))
    if alert is None:
        raise HTTPException(status_code=404, detail="alert not found")

    alert.is_dismissed = True
    alert.dismissed_at = _utc_now()
    await db.commit()
    return {"message": "alert dismissed"}


@router.get("/manager/developer/{username}/history")
async def manager_developer_history(
    username: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    org_id = str(current_user.org_id)

    user_row = await db.scalar(
        select(User).where(and_(User.github_username == username, User.org_id == current_user.org_id))
    )

    notes_by_commit: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if user_row is not None:
        notes = await db.scalars(
            select(CommitContextNote)
            .where(CommitContextNote.developer_id == user_row.id)
            .order_by(desc(CommitContextNote.created_at))
        )
        for note in notes.all():
            notes_by_commit[note.commit_sha].append(
                {
                    "id": str(note.id),
                    "context_note": note.context_note,
                    "created_at": note.created_at,
                }
            )

    scores = await db.scalars(
        select(CommitScore)
        .where(and_(CommitScore.org_id == org_id, CommitScore.developer == username))
        .order_by(desc(CommitScore.created_at))
    )

    return [
        {
            "commit_sha": s.commit_sha,
            "score": s.score,
            "confidence": s.confidence,
            "breakdown": _score_breakdown(s),
            "plain_english": s.plain_english,
            "created_at": s.created_at,
            "context_notes": notes_by_commit.get(s.commit_sha, []),
        }
        for s in scores.all()
    ]


def _maybe_update_chromadb(org_id: str, username: str, specialty_text: str) -> bool:
    try:
        import chromadb  # type: ignore
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception:
        return False

    model = SentenceTransformer("all-MiniLM-L6-v2")
    vector = model.encode([specialty_text])[0].tolist()

    client = chromadb.PersistentClient(path=".chromadb")
    collection = client.get_or_create_collection(name="developer_skills")
    collection.upsert(
        ids=[f"{org_id}:{username}"],
        embeddings=[vector],
        documents=[specialty_text],
        metadatas=[{"org_id": org_id, "username": username}],
    )
    return True


@router.post("/manager/developer/{username}/specialty")
async def manager_update_specialty(
    username: str,
    payload: SpecialtyRequest,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    org_id = str(current_user.org_id)
    dev = await db.scalar(select(Developer).where(and_(Developer.org_id == org_id, Developer.username == username)))
    if dev is None:
        raise HTTPException(status_code=404, detail="developer not found")

    dev.specialties = payload.specialty_text.strip()
    await db.commit()

    vector_ok = _maybe_update_chromadb(org_id, username, payload.specialty_text.strip())
    return {
        "message": "specialty updated",
        "vector_store": "updated" if vector_ok else "skipped",
    }


def _fallback_similarity(query: str, text: str) -> float:
    q = set(_tokenize(query))
    t = set(_tokenize(text))
    if not q or not t:
        return 0.0
    return len(q.intersection(t)) / len(q.union(t))


@router.get("/manager/project-match")
async def manager_project_match(
    requirements: str = Query(..., min_length=3),
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    org_id = str(current_user.org_id)

    try:
        import chromadb  # type: ignore
        from sentence_transformers import SentenceTransformer  # type: ignore

        model = SentenceTransformer("all-MiniLM-L6-v2")
        query_vec = model.encode([requirements])[0].tolist()

        client = chromadb.PersistentClient(path=".chromadb")
        collection = client.get_or_create_collection(name="developer_skills")
        hit = collection.query(
            query_embeddings=[query_vec],
            n_results=5,
            where={"org_id": org_id},
            include=["documents", "metadatas", "distances"],
        )

        docs = hit.get("documents", [[]])[0]
        metas = hit.get("metadatas", [[]])[0]
        dists = hit.get("distances", [[]])[0]

        results: List[Dict[str, Any]] = []
        for idx in range(min(len(docs), len(metas), len(dists))):
            meta = metas[idx] or {}
            distance = float(dists[idx])
            match_score = max(0.0, min(1.0, 1.0 - distance))
            results.append(
                {
                    "developer": meta.get("username"),
                    "match_score": round(match_score, 4),
                    "matching_skills": docs[idx],
                }
            )
        return results
    except Exception:
        devs = await db.scalars(select(Developer).where(Developer.org_id == org_id))
        scored: List[Tuple[Developer, float]] = []
        for dev in devs.all():
            text = str(dev.specialties or "")
            sim = _fallback_similarity(requirements, text)
            scored.append((dev, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {
                "developer": d.username,
                "match_score": round(score, 4),
                "matching_skills": d.specialties or "",
            }
            for d, score in scored[:5]
        ]


@router.post("/manager/commits/{commit_sha}/assign-ticket")
async def manager_assign_ticket(
    commit_sha: str,
    payload: AssignTicketRequest,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    org_id = str(current_user.org_id)
    commit = await db.scalar(
        select(CommitScore).where(and_(CommitScore.org_id == org_id, CommitScore.commit_sha == commit_sha))
    )
    if commit is None:
        raise HTTPException(status_code=404, detail="commit not found")

    commit.ticket_id = payload.ticket_id.strip()
    await db.commit()

    repo = await _org_github_repo(db, current_user.org_id)
    if not repo:
        raise HTTPException(status_code=400, detail="org repository not configured")

    from tasks import process_commit

    process_commit.delay(
        {
            "org_id": commit.org_id,
            "developer": commit.developer,
            "branch": commit.branch or "",
            "commit_sha": commit.commit_sha,
            "repo": repo,
            "ticket_id": commit.ticket_id,
        }
    )

    return {"message": "ticket assigned, rescoring in progress"}


@router.get("/ceo/org/heatmap")
async def ceo_org_heatmap(
    current_user: User = Depends(require_ceo),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, List[Dict[str, Any]]]:
    org_id = str(current_user.org_id)

    devs = await db.scalars(select(Developer).where(Developer.org_id == org_id))
    buckets: Dict[str, List[Dict[str, Any]]] = {"high": [], "medium": [], "low": []}

    for dev in devs.all():
        latest = await db.scalar(
            select(CommitScore)
            .where(and_(CommitScore.org_id == org_id, CommitScore.developer == dev.username))
            .order_by(desc(CommitScore.created_at))
            .limit(1)
        )

        score_val = float(latest.score) if latest and latest.score is not None else 0.0
        if score_val >= 70:
            bucket = "high"
        elif score_val >= 40:
            bucket = "medium"
        else:
            bucket = "low"

        buckets[bucket].append(
            {
                "developer": dev.username,
                "score": score_val,
                "burnout_risk": dev.burnout_risk,
                "knowledge_risk": not bool((dev.specialties or "").strip()),
            }
        )

    return buckets


@router.get("/ceo/org/health")
async def ceo_org_health(
    current_user: User = Depends(require_ceo),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    org_id = str(current_user.org_id)

    avg_team_score = await db.scalar(
        select(func.avg(CommitScore.score)).where(and_(CommitScore.org_id == org_id, CommitScore.score.is_not(None)))
    )

    burnout_risk_count = await db.scalar(
        select(func.count(Developer.id)).where(and_(Developer.org_id == org_id, Developer.burnout_risk == "high"))
    )

    active_blocker_count = await db.scalar(
        select(func.count(Alert.id)).where(
            and_(Alert.org_id == org_id, Alert.is_dismissed.is_(False), Alert.alert_type == "blocker")
        )
    )

    knowledge_risk_count = await db.scalar(
        select(func.count(Alert.id)).where(
            and_(Alert.org_id == org_id, Alert.is_dismissed.is_(False), Alert.alert_type == "knowledge_risk")
        )
    )

    ws = _week_start()
    week_start_dt = datetime.combine(ws, datetime.min.time(), tzinfo=timezone.utc)

    rows = await db.execute(
        select(CommitScore.developer, func.avg(CommitScore.score).label("avg_score"))
        .where(
            and_(
                CommitScore.org_id == org_id,
                CommitScore.score.is_not(None),
                CommitScore.created_at >= week_start_dt,
            )
        )
        .group_by(CommitScore.developer)
        .order_by(desc("avg_score"))
        .limit(3)
    )

    top_performers = [
        {
            "developer": r[0],
            "avg_score": float(r[1]) if r[1] is not None else None,
            "achievement": "Top weekly performer",
        }
        for r in rows.fetchall()
    ]

    team_size = await db.scalar(select(func.count(Developer.id)).where(Developer.org_id == org_id))

    return {
        "avg_team_score": float(avg_team_score) if avg_team_score is not None else 0.0,
        "burnout_risk_count": int(burnout_risk_count or 0),
        "active_blocker_count": int(active_blocker_count or 0),
        "knowledge_risk_count": int(knowledge_risk_count or 0),
        "top_performers": top_performers,
        "team_size": int(team_size or 0),
    }


@router.get("/ceo/org/knowledge-risk")
async def ceo_knowledge_risk(
    current_user: User = Depends(require_ceo),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    org_id = str(current_user.org_id)

    commits = await db.scalars(
        select(CommitScore).where(and_(CommitScore.org_id == org_id, CommitScore.branch.is_not(None)))
    )

    branch_contributors: Dict[str, set] = defaultdict(set)
    rows_by_dev: Dict[str, List[CommitScore]] = defaultdict(list)

    for row in commits.all():
        module = (row.branch or "unknown").strip() or "unknown"
        branch_contributors[module].add(row.developer)
        rows_by_dev[row.developer].append(row)

    devs = await db.scalars(select(Developer).where(Developer.org_id == org_id))
    burnout_map = {d.username: (d.burnout_risk or "low") for d in devs.all()}

    output: List[Dict[str, Any]] = []
    for developer, rows in rows_by_dev.items():
        module_counts: Counter[str] = Counter((r.branch or "unknown").strip() or "unknown" for r in rows)
        module = module_counts.most_common(1)[0][0]
        bus_factor = len(branch_contributors[module])
        burnout = burnout_map.get(developer, "low")

        if bus_factor <= 1 and burnout == "high":
            level = "critical"
        elif bus_factor <= 1 or burnout == "high":
            level = "high"
        else:
            level = "medium"

        output.append(
            {
                "developer": developer,
                "module": module,
                "bus_factor": bus_factor,
                "burnout_risk": burnout,
                "risk_level": level,
            }
        )

    rank = {"critical": 0, "high": 1, "medium": 2}
    output.sort(key=lambda x: (rank.get(x["risk_level"], 3), x["bus_factor"]))
    return output


@router.get("/ceo/org/skill-gaps")
async def ceo_skill_gaps(
    current_user: User = Depends(require_ceo),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    org_id = str(current_user.org_id)

    devs = await db.scalars(select(Developer).where(Developer.org_id == org_id))
    specialties_text = " ".join((d.specialties or "") for d in devs.all()).lower()

    covered = [domain for domain in _COMMON_DOMAINS if domain in specialties_text]
    gaps = [domain for domain in _COMMON_DOMAINS if domain not in covered]

    recommendation = f"Consider hiring {gaps[0]} skill" if gaps else "Current team covers key baseline domains"
    return {"covered": covered, "gaps": gaps, "recommendation": recommendation}


@router.get("/ceo/org/trends")
async def ceo_org_trends(
    weeks: int = Query(default=8, ge=1, le=52),
    current_user: User = Depends(require_ceo),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    org_id = str(current_user.org_id)
    cutoff = _week_start() - timedelta(weeks=weeks - 1)

    rows = await db.scalars(
        select(WeeklySnapshot)
        .where(and_(WeeklySnapshot.org_id == org_id, WeeklySnapshot.week_start >= cutoff))
        .order_by(WeeklySnapshot.week_start)
    )

    return [
        {
            "week_start": r.week_start,
            "avg_team_score": r.avg_team_score,
            "burnout_risk_count": r.burnout_risk_count,
            "blocker_count": r.blocker_count,
            "top_performer": r.top_performer_username,
        }
        for r in rows.all()
    ]


def _build_report_pdf(file_path: Path, health: Dict[str, Any], trends: List[Dict[str, Any]], skill_gaps: Dict[str, Any]) -> None:
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.shapes import Drawing
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(file_path), pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 50, "DevIQ Executive Report")

    c.setFont("Helvetica", 11)
    c.drawString(40, height - 80, f"Average Team Score: {health.get('avg_team_score', 0):.2f}")
    c.drawString(40, height - 98, f"Burnout Risk Count: {health.get('burnout_risk_count', 0)}")
    c.drawString(40, height - 116, f"Active Blockers: {health.get('active_blocker_count', 0)}")
    c.drawString(40, height - 134, f"Knowledge Risks: {health.get('knowledge_risk_count', 0)}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, height - 168, "Top Performers")
    c.setFont("Helvetica", 10)
    y = height - 186
    for item in health.get("top_performers", []):
        c.drawString(46, y, f"- {item.get('developer')}: {item.get('avg_score')}")
        y -= 14

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y - 10, "Skill Gaps")
    c.setFont("Helvetica", 10)
    c.drawString(46, y - 28, f"Covered: {', '.join(skill_gaps.get('covered', [])) or 'none'}")
    c.drawString(46, y - 44, f"Gaps: {', '.join(skill_gaps.get('gaps', [])) or 'none'}")
    c.drawString(46, y - 60, f"Recommendation: {skill_gaps.get('recommendation', '')}")

    chart_data = [float(t.get("avg_team_score") or 0.0) for t in trends[-8:]]
    if chart_data:
        drawing = Drawing(480, 170)
        chart = VerticalBarChart()
        chart.x = 40
        chart.y = 25
        chart.height = 120
        chart.width = 400
        chart.data = [chart_data]
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max(100, int(max(chart_data) + 10))
        chart.valueAxis.valueStep = 10
        chart.categoryAxis.labels.angle = 30
        chart.categoryAxis.categoryNames = [str(t.get("week_start")) for t in trends[-8:]]
        drawing.add(chart)

        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, 220, "Week-over-Week Trend")
        drawing.drawOn(c, 40, 30)

    c.save()


@router.get("/ceo/org/report")
async def ceo_org_report(
    current_user: User = Depends(require_ceo),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    # Reuse route logic through direct DB queries for report payload.
    health = await ceo_org_health(current_user=current_user, db=db)
    trends = await ceo_org_trends(current_user=current_user, db=db)
    skill_gaps = await ceo_skill_gaps(current_user=current_user, db=db)

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).date().isoformat()
    filename = f"deviq_report_{current_user.org_id}_{today}.pdf"
    file_path = reports_dir / filename

    try:
        _build_report_pdf(file_path, health, trends, skill_gaps)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"failed to generate report: {exc}") from exc

    return FileResponse(path=str(file_path), media_type="application/pdf", filename=filename)
