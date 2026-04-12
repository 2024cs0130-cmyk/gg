import asyncio

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from models import Base, engine


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    org_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    github_username = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('developer', 'manager', 'ceo')", name="ck_users_role_values"),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    is_revoked = Column(Boolean, nullable=False, server_default=text("false"))


class CommitContextNote(Base):
    __tablename__ = "commit_context_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    commit_sha = Column(String, nullable=False)
    developer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    context_note = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    org_id = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)
    developer_username = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    severity = Column(String, nullable=False)
    is_dismissed = Column(Boolean, nullable=False, server_default=text("false"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    dismissed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "alert_type IN ('blocker', 'burnout', 'knowledge_risk', 'unlinked_commit')",
            name="ck_alerts_alert_type_values",
        ),
        CheckConstraint("severity IN ('high', 'medium', 'low')", name="ck_alerts_severity_values"),
    )


class WeeklySnapshot(Base):
    __tablename__ = "weekly_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    org_id = Column(String, nullable=False)
    week_start = Column(Date, nullable=False)
    avg_team_score = Column(Float, nullable=True)
    burnout_risk_count = Column(Integer, nullable=False, server_default=text("0"))
    blocker_count = Column(Integer, nullable=False, server_default=text("0"))
    knowledge_risk_count = Column(Integer, nullable=False, server_default=text("0"))
    top_performer_username = Column(String, nullable=True)
    top_performer_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


async def create_auth_schema() -> None:
    async with engine.begin() as conn:
        # Create all mapped tables that share Base metadata.
        await conn.run_sync(Base.metadata.create_all)

        # Existing table update for developer-first visibility flow.
        await conn.execute(
            text(
                "ALTER TABLE commit_scores "
                "ADD COLUMN IF NOT EXISTS developer_seen BOOLEAN DEFAULT FALSE"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE commit_scores "
                "ADD COLUMN IF NOT EXISTS developer_seen_at TIMESTAMPTZ NULL"
            )
        )


if __name__ == "__main__":
    asyncio.run(create_auth_schema())
