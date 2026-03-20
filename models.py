import os
import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class CommitScore(Base):
    __tablename__ = "commit_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(String, nullable=False)
    developer = Column(String, nullable=False)
    commit_sha = Column(String, unique=True, nullable=False)
    branch = Column(String, nullable=True)
    ticket_id = Column(String, nullable=True)
    score = Column(Float, nullable=True)
    relevance = Column(Float, nullable=True)
    impact = Column(Float, nullable=True)
    complexity = Column(Float, nullable=True)
    glue_work = Column(Float, nullable=True)
    confidence = Column(String, nullable=True)
    plain_english = Column(Text, nullable=True)
    diff_translation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="ck_commit_scores_score_range"),
        CheckConstraint(
            "confidence IS NULL OR confidence IN ('high', 'medium', 'low', 'uncertain')",
            name="ck_commit_scores_confidence_values",
        ),
    )


class Developer(Base):
    __tablename__ = "developers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(String, nullable=False)
    username = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    total_commits = Column(Integer, nullable=False, server_default="0")
    avg_score = Column(Float, nullable=True)
    last_active = Column(DateTime(timezone=True), nullable=True)
    specialties = Column(Text, nullable=True)
    burnout_risk = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "burnout_risk IS NULL OR burnout_risk IN ('low', 'medium', 'high')",
            name="ck_developers_burnout_risk_values",
        ),
    )


class Organisation(Base):
    __tablename__ = "organisations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True)
    github_repo = Column(String, nullable=True)
    jira_workspace = Column(String, nullable=True)
    encrypted_github_token = Column(Text, nullable=True)
    encrypted_jira_token = Column(Text, nullable=True)
    tier = Column(String, nullable=False, server_default="starter")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(String, nullable=False)
    service = Column(String, nullable=False)
    encrypted_token = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("org_id", "service", name="uq_api_keys_org_service"),
        CheckConstraint("service IN ('github', 'jira')", name="ck_api_keys_service_values"),
        CheckConstraint("length(org_id) > 0", name="ck_api_keys_org_id_nonempty"),
    )


DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

# Normalize common Postgres URL format for SQLAlchemy async engine.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine: AsyncEngine = create_async_engine(DATABASE_URL, future=True)


async def create_all() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
