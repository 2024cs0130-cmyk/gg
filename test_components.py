import asyncio
import os
from typing import Callable, List, Tuple

from dotenv import load_dotenv


load_dotenv()


def test_redis_connection() -> bool:
    try:
        from redis import Redis

        redis_url = os.getenv("REDIS_URL", "").strip()
        if not redis_url:
            raise RuntimeError("REDIS_URL is missing")

        client = Redis.from_url(redis_url, decode_responses=True)
        if client.ping() is True:
            print("PASS: Redis connected")
            return True

        print("FAIL: Redis not running")
        return False
    except Exception:
        print("FAIL: Redis not running")
        return False


def test_database_connection() -> bool:
    async def _check_db() -> None:
        from sqlalchemy import text

        from models import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    try:
        asyncio.run(_check_db())
        print("PASS: Database connected")
        return True
    except Exception as error:
        print(f"FAIL: Database error: {error}")
        return False


def test_jira_connection() -> bool:
    try:
        from jira import JIRA

        ticket_id = os.getenv("JIRA_TEST_TICKET", "DEV-1").strip() or "DEV-1"
        jira_url = os.getenv("JIRA_URL", "").strip()
        jira_email = os.getenv("JIRA_EMAIL", "").strip()
        jira_api_token = os.getenv("JIRA_API_TOKEN", "").strip()

        if not jira_url or not jira_email or not jira_api_token:
            raise RuntimeError("JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN environment variables are required")

        jira_client = JIRA(server=jira_url, basic_auth=(jira_email, jira_api_token))
        issue = jira_client.issue(ticket_id, fields="summary")
        title = str(getattr(issue.fields, "summary", "")).strip() or "(no title)"
        print(f"PASS: Jira connected, ticket title: {title}")
        return True
    except Exception as error:
        print(f"FAIL: Jira error: {error}")
        return False


def test_github_connection() -> bool:
    try:
        from github import Github

        from github_fetcher import get_diff

        repo_name = os.getenv("GITHUB_TEST_REPO", "").strip()
        if not repo_name:
            raise RuntimeError("GITHUB_TEST_REPO is missing")

        token_env = os.getenv("GITHUB_TOKENS", "").strip()
        if token_env:
            token = token_env.split(",")[0].strip()
        else:
            token = os.getenv("GITHUB_TOKEN", "").strip()

        if not token:
            raise RuntimeError("GITHUB_TOKEN or GITHUB_TOKENS is missing")

        gh = Github(token, per_page=1)
        repo = gh.get_repo(repo_name)
        latest_commit = next(iter(repo.get_commits()), None)
        if latest_commit is None:
            raise RuntimeError("No commits found in repository")

        diff = get_diff(repo_name, latest_commit.sha)
        diff_length = len(str(diff.get("diff_text", "")))
        print(f"PASS: GitHub connected, diff length: {diff_length}")
        return True
    except Exception as error:
        print(f"FAIL: GitHub error: {error}")
        return False


def test_effort_engine() -> bool:
    try:
        from effort_engine import score

        diff_text = "def login(): validate() return jwt()"
        jira_context = "Build login with email validation"
        result = score(diff_text, jira_context, developer="test-user", commit_metadata={})

        score_value = float(result.get("score", -1))
        if 0 <= score_value <= 100:
            print(f"PASS: Effort engine works, score: {score_value}")
            return True

        raise AssertionError(f"score out of range: {score_value}")
    except Exception as error:
        print(f"FAIL: Engine error: {error}")
        return False


def test_key_manager() -> bool:
    try:
        from key_manager import decrypt_key, encrypt_key

        raw = "test_token_123"
        encrypted = encrypt_key(raw)
        decrypted = decrypt_key(encrypted)

        if decrypted != raw:
            raise AssertionError("decrypted token does not match original")

        print("PASS: Key encryption works")
        return True
    except Exception as error:
        print(f"FAIL: Encryption error: {error}")
        return False


def test_celery_connection() -> bool:
    try:
        from celery_app import celery_app

        responses = celery_app.control.ping(timeout=2.0) or []
        if len(responses) > 0:
            print("PASS: Celery worker running")
            return True

        print("FAIL: No Celery workers found - start with: celery -A celery_app worker")
        return False
    except Exception:
        print("FAIL: No Celery workers found - start with: celery -A celery_app worker")
        return False


def main() -> None:
    tests: List[Tuple[str, Callable[[], bool]]] = [
        ("Redis connection", test_redis_connection),
        ("Database connection", test_database_connection),
        ("Jira connection", test_jira_connection),
        ("GitHub connection", test_github_connection),
        ("Effort engine", test_effort_engine),
        ("Key manager", test_key_manager),
        ("Celery connection", test_celery_connection),
    ]

    passed = 0
    for _, test_fn in tests:
        if test_fn():
            passed += 1

    print(f"{passed}/7 tests passed")
    if passed == 7:
        print("BACKEND READY")


if __name__ == "__main__":
    main()
