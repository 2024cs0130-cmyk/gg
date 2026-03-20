import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Union

from github import Github
from github.GithubException import GithubException, RateLimitExceededException
from redis import Redis


REDIS_URL = os.getenv("REDIS_URL", "").strip()
if not REDIS_URL:
    raise RuntimeError("REDIS_URL environment variable is required")

_redis = Redis.from_url(REDIS_URL, decode_responses=True)


def _get_tokens() -> List[str]:
    tokens_env = os.getenv("GITHUB_TOKENS", "").strip()
    if tokens_env:
        tokens = [token.strip() for token in tokens_env.split(",") if token.strip()]
    else:
        token = os.getenv("GITHUB_TOKEN", "").strip()
        tokens = [token] if token else []

    if not tokens:
        raise RuntimeError("GITHUB_TOKEN or GITHUB_TOKENS environment variable is required")

    return tokens


def _select_token_round_robin() -> str:
    tokens = _get_tokens()
    if len(tokens) == 1:
        return tokens[0]

    counter = _redis.incr("github:token:round_robin")
    index = (counter - 1) % len(tokens)
    return tokens[index]


def _get_github_client() -> Github:
    return Github(_select_token_round_robin(), per_page=100)


def _rate_limit_wait_seconds(exc: GithubException, client: Github, attempt: int) -> int:
    headers = getattr(exc, "headers", {}) or {}
    reset_header = headers.get("x-ratelimit-reset") or headers.get("X-RateLimit-Reset")

    if reset_header:
        try:
            reset_ts = int(reset_header)
            return max(reset_ts - int(time.time()) + 1, 1)
        except (TypeError, ValueError):
            pass

    try:
        reset_dt = client.get_rate_limit().core.reset
        if reset_dt is not None:
            now_utc = datetime.now(timezone.utc)
            if reset_dt.tzinfo is None:
                reset_dt = reset_dt.replace(tzinfo=timezone.utc)
            return max(int((reset_dt - now_utc).total_seconds()) + 1, 1)
    except Exception:
        pass

    return min(2 ** attempt, 60)


def _with_rate_limit_retry(operation: Callable[[Github], Any], max_attempts: int = 6) -> Any:
    attempt = 0

    while True:
        client = _get_github_client()
        try:
            return operation(client)
        except RateLimitExceededException as exc:
            attempt += 1
            if attempt >= max_attempts:
                raise
            time.sleep(_rate_limit_wait_seconds(exc, client, attempt))
        except GithubException as exc:
            is_rate_limit_error = exc.status == 403 and "rate limit" in str(exc).lower()
            if not is_rate_limit_error:
                raise

            attempt += 1
            if attempt >= max_attempts:
                raise
            time.sleep(_rate_limit_wait_seconds(exc, client, attempt))


def _parse_since_date(since_date: Union[str, datetime]) -> datetime:
    if isinstance(since_date, datetime):
        parsed = since_date
    else:
        normalized = since_date.strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def get_diff(repo_name: str, commit_sha: str) -> Dict[str, Any]:
    cache_key = commit_sha
    cached = _redis.get(cache_key)
    if cached:
        return json.loads(cached)

    def _fetch(client: Github) -> Dict[str, Any]:
        repo = client.get_repo(repo_name)
        commit = repo.get_commit(commit_sha)
        changed_files = list(commit.files)

        patches: List[str] = []
        lines_added = 0
        lines_deleted = 0
        is_new_file = False

        for changed in changed_files:
            patch_text = getattr(changed, "patch", None)
            if patch_text:
                patches.append(patch_text)

            lines_added += int(getattr(changed, "additions", 0) or 0)
            lines_deleted += int(getattr(changed, "deletions", 0) or 0)

            if str(getattr(changed, "status", "")).lower() == "added":
                is_new_file = True

        return {
            "diff_text": "\n\n".join(patches),
            "files_changed": len(changed_files),
            "changed_files": [str(getattr(changed, "filename", "")) for changed in changed_files],
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "is_new_file": is_new_file,
        }

    result = _with_rate_limit_retry(_fetch)
    _redis.setex(cache_key, 1800, json.dumps(result))
    return result


def get_pr_reviews(developer_username: str, since_date: Union[str, datetime]) -> List[Dict[str, Any]]:
    since_dt = _parse_since_date(since_date)
    since_query = since_dt.date().isoformat()
    query = f"type:pr commenter:{developer_username} updated:>={since_query}"

    def _fetch(client: Github) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        search_results = client.search_issues(query=query, sort="updated", order="desc")

        for issue in search_results:
            pull_request = issue.as_pull_request()
            for comment in pull_request.get_review_comments():
                comment_user = getattr(comment.user, "login", "")
                if comment_user.lower() != developer_username.lower():
                    continue

                created_at = comment.created_at
                if created_at is None:
                    continue
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                if created_at < since_dt:
                    continue

                results.append(
                    {
                        "repo_name": pull_request.base.repo.full_name,
                        "pull_number": pull_request.number,
                        "comment_id": comment.id,
                        "path": comment.path,
                        "body": comment.body,
                        "commit_id": comment.commit_id,
                        "html_url": comment.html_url,
                        "created_at": created_at.isoformat(),
                        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
                    }
                )

        return results

    return _with_rate_limit_retry(_fetch)
