import asyncio
import os
import uuid
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker


load_dotenv()

# Import requested existing modules after loading .env.
import auth
import auth_models
import models


TEST_ORG_SLUG = "test-org-001"
TEST_ORG_ID = uuid.uuid5(uuid.NAMESPACE_DNS, TEST_ORG_SLUG)


def _repo_owner(repo_full_name: str) -> Optional[str]:
    parts = (repo_full_name or "").split("/", 1)
    if parts and parts[0].strip():
        return parts[0].strip()
    return None


def _print_summary() -> None:
    print("================================")
    print("DEVIQ TEST ACCOUNTS")
    print("================================")
    print("Developer : developer@deviq.test / DevTest123!")
    print("Manager   : manager@deviq.test   / MgrTest123!")
    print("CEO       : ceo@deviq.test       / CeoTest123!")
    print("================================")
    print("Login at: POST http://localhost:8000/auth/login")
    print("================================")


async def seed() -> None:
    github_repo = os.getenv("GITHUB_TEST_REPO", "").strip()
    jira_workspace = os.getenv("JIRA_URL", "").strip()
    github_owner = _repo_owner(github_repo) or "test-owner"

    session_factory = async_sessionmaker(models.engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            # Step 1: Create test organisation if missing.
            org = await session.scalar(select(models.Organisation).where(models.Organisation.id == TEST_ORG_ID))
            if org is None:
                org = models.Organisation(
                    id=TEST_ORG_ID,
                    name="Test Company",
                    github_repo=github_repo or None,
                    jira_workspace=jira_workspace or None,
                )
                session.add(org)
                print(f"Created organisation: {TEST_ORG_SLUG} ({TEST_ORG_ID})")
            else:
                print(f"Organisation exists: {TEST_ORG_SLUG} ({TEST_ORG_ID})")

            # Ensure a corresponding developer profile row exists for manager dashboards.
            developer_profile = await session.scalar(
                select(models.Developer).where(
                    and_(
                        models.Developer.org_id == str(TEST_ORG_ID),
                        models.Developer.username == github_owner,
                    )
                )
            )
            if developer_profile is None:
                session.add(
                    models.Developer(
                        org_id=str(TEST_ORG_ID),
                        username=github_owner,
                        display_name="Rajan Kumar",
                        email="developer@deviq.test",
                        burnout_risk="high",
                    )
                )

            # Step 2: Create users (skip if existing by email).
            users_to_seed = [
                {
                    "email": "developer@deviq.test",
                    "password": "DevTest123!",
                    "role": "developer",
                    "display_name": "Rajan Kumar",
                    "github_username": github_owner,
                },
                {
                    "email": "manager@deviq.test",
                    "password": "MgrTest123!",
                    "role": "manager",
                    "display_name": "Priya Sharma",
                    "github_username": None,
                },
                {
                    "email": "ceo@deviq.test",
                    "password": "CeoTest123!",
                    "role": "ceo",
                    "display_name": "Arjun Malhothra",
                    "github_username": None,
                },
            ]

            for entry in users_to_seed:
                existing_user = await session.scalar(
                    select(auth_models.User).where(auth_models.User.email == entry["email"])
                )
                if existing_user is not None:
                    existing_user.role = entry["role"]
                    existing_user.display_name = entry["display_name"]
                    existing_user.github_username = entry["github_username"]
                    existing_user.is_active = True
                    print(f"User exists, updated: {entry['email']}")
                    continue

                session.add(
                    auth_models.User(
                        org_id=TEST_ORG_ID,
                        email=entry["email"],
                        hashed_password=auth.hash_password(entry["password"]),
                        role=entry["role"],
                        display_name=entry["display_name"],
                        github_username=entry["github_username"],
                        is_active=True,
                    )
                )
                print(f"Created user: {entry['email']}")

            # Step 3: Create sample alerts for testing (skip duplicates by type + message + org).
            alert_specs = [
                {
                    "alert_type": "blocker",
                    "developer_username": "Rajan",
                    "message": "Ticket DEV-1 blocked for 52 hours (Rajan)",
                    "severity": "high",
                },
                {
                    "alert_type": "burnout",
                    "developer_username": "Rajan",
                    "message": "Rajan effort dropped 35% over the last 2 weeks",
                    "severity": "high",
                },
                {
                    "alert_type": "knowledge_risk",
                    "developer_username": "Rajan",
                    "message": "Rajan owns 80% of auth module and has high burnout risk",
                    "severity": "high",
                },
            ]

            for spec in alert_specs:
                existing_alert = await session.scalar(
                    select(auth_models.Alert).where(
                        and_(
                            auth_models.Alert.org_id == str(TEST_ORG_ID),
                            auth_models.Alert.alert_type == spec["alert_type"],
                            auth_models.Alert.message == spec["message"],
                            auth_models.Alert.is_dismissed.is_(False),
                        )
                    )
                )
                if existing_alert is not None:
                    print(f"Alert exists, skipped: {spec['alert_type']}")
                    continue

                session.add(
                    auth_models.Alert(
                        org_id=str(TEST_ORG_ID),
                        alert_type=spec["alert_type"],
                        developer_username=spec["developer_username"],
                        message=spec["message"],
                        severity=spec["severity"],
                    )
                )
                print(f"Created alert: {spec['alert_type']}")

            await session.commit()

    except SQLAlchemyError as exc:
        print(f"Database error during seed: {exc}")
        return
    except Exception as exc:
        print(f"Unexpected error during seed: {exc}")
        return

    _print_summary()


if __name__ == "__main__":
    asyncio.run(seed())
