import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence

from rank_bm25 import BM25Okapi

import github_fetcher


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\b\w+\b", (text or "").lower())


def _safe_datetime(value: Optional[Any], default: datetime) -> datetime:
    if value is None:
        return default
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        return default

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _vector_to_list(vec: Any) -> List[float]:
    if hasattr(vec, "tolist"):
        vec = vec.tolist()

    if not isinstance(vec, Sequence):
        raise ValueError("Encoded embedding must be a sequence")

    result: List[float] = []
    for item in vec:
        try:
            result.append(float(item))
        except (TypeError, ValueError):
            result.append(0.0)
    return result


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0

    limit = min(len(a), len(b))
    if limit == 0:
        return 0.0

    dot = 0.0
    mag_a = 0.0
    mag_b = 0.0
    for i in range(limit):
        av = float(a[i])
        bv = float(b[i])
        dot += av * bv
        mag_a += av * av
        mag_b += bv * bv

    if mag_a <= 0 or mag_b <= 0:
        return 0.0

    return max(min(dot / ((mag_a ** 0.5) * (mag_b ** 0.5)), 1.0), -1.0)


def _normalize_bm25(raw_score: float) -> float:
    # Saturating normalization that keeps score in [0, 1).
    return raw_score / (raw_score + 1.0) if raw_score > 0 else 0.0


def _translator_to_plain_english(diff_text: str) -> str:
    import translator

    for fn_name in (
        "convert_diff_to_english",
        "translate_diff_to_english",
        "translate_diff",
        "diff_to_plain_english",
    ):
        fn = getattr(translator, fn_name, None)
        if callable(fn):
            return str(fn(diff_text)).strip()

    raise AttributeError(
        "translator.py must expose one of: convert_diff_to_english, "
        "translate_diff_to_english, translate_diff, diff_to_plain_english"
    )


def _llm_validate_description(diff_text: str, description: str) -> str:
    import ai_engine

    prompt = (
        "Does this description match this code diff? "
        "Reply with exactly one token: ACCURATE, INACCURATE, or UNCERTAIN.\n\n"
        f"CODE_DIFF:\n{diff_text}\n\n"
        f"DESCRIPTION:\n{description}\n"
    )

    validators = (
        getattr(ai_engine, "validate_description_match", None),
        getattr(ai_engine, "ask_llm", None),
        getattr(ai_engine, "chat", None),
        getattr(ai_engine, "generate", None),
    )

    for validator in validators:
        if callable(validator):
            response = str(validator(prompt)).upper()
            if "INACCURATE" in response:
                return "INACCURATE"
            if "ACCURATE" in response:
                return "ACCURATE"
            if "UNCERTAIN" in response:
                return "UNCERTAIN"

    return "UNCERTAIN"


def _embed_text(text: str) -> List[float]:
    import ai_engine

    model = getattr(ai_engine, "model", None)
    if model is None or not hasattr(model, "encode"):
        raise AttributeError("ai_engine.py must expose model.encode()")

    vector = model.encode(text)
    return _vector_to_list(vector)


def _compute_relevance(diff_text: str, jira_context: str) -> Dict[str, Any]:
    plain_english = _translator_to_plain_english(diff_text)

    first_pass = _llm_validate_description(diff_text, plain_english)
    second_pass = _llm_validate_description(diff_text, plain_english)

    validation = second_pass if second_pass == first_pass else "UNCERTAIN"

    if validation == "INACCURATE":
        return {
            "relevance": 0.0,
            "confidence": "low",
            "flag": "needs_review",
            "plain_english": plain_english,
            "cosine": 0.0,
            "bm25": 0.0,
            "validation": validation,
        }

    description_vec = _embed_text(plain_english)
    jira_vec = _embed_text(jira_context)

    cosine = _cosine_similarity(description_vec, jira_vec)
    cosine_normalized = (cosine + 1.0) / 2.0

    jira_tokens = _tokenize(jira_context)
    description_tokens = _tokenize(plain_english)
    bm25_engine = BM25Okapi([jira_tokens or ["empty"]])
    bm25_raw = float(bm25_engine.get_scores(description_tokens or ["empty"])[0])
    bm25_normalized = _normalize_bm25(bm25_raw)

    confidence = "high"
    if abs(cosine_normalized - bm25_normalized) > 0.3 or validation == "UNCERTAIN":
        confidence = "uncertain"

    relevance = (cosine_normalized * 0.6) + (bm25_normalized * 0.4)
    return {
        "relevance": max(min(relevance, 1.0), 0.0),
        "confidence": confidence,
        "flag": None,
        "plain_english": plain_english,
        "cosine": cosine_normalized,
        "bm25": bm25_normalized,
        "validation": validation,
    }


def _compute_impact(
    files_changed: int,
    changed_files: Optional[Iterable[str]],
    core_files: Optional[Iterable[str]],
    old_coverage: float,
    new_coverage: float,
) -> float:
    changed_files_set = {f for f in (changed_files or [])}
    core_files_set = {f for f in (core_files or [])}

    is_core_file = 1.0 if any(path in core_files_set for path in changed_files_set) else 0.0
    coverage_delta = max(new_coverage - old_coverage, 0.0)

    score = (files_changed * 0.3) + (is_core_file * 0.4) + (coverage_delta * 0.3)
    return max(min(score, 1.0), 0.0)


def _compute_complexity(
    commit_date: Optional[Any],
    ticket_in_progress_date: Optional[Any],
    additions: int,
    deletions: int,
) -> float:
    now_utc = datetime.now(timezone.utc)
    commit_dt = _safe_datetime(commit_date, now_utc)
    ticket_dt = _safe_datetime(ticket_in_progress_date, commit_dt - timedelta(days=1))

    days_open = max((commit_dt - ticket_dt).days, 1)
    lines_changed = max(int(additions) + int(deletions), 1)

    ratio = days_open / (lines_changed / 10.0)
    return max(min(ratio / 5.0, 1.0), 0.0)


def _word_count(text: str) -> int:
    return len(_tokenize(text))


def _count_unblock_signals(
    reviews: List[Dict[str, Any]],
    developer_username: str,
    review_window_hours: int = 2,
) -> int:
    token = os.getenv("GITHUB_TOKEN", "").strip() or (
        os.getenv("GITHUB_TOKENS", "").split(",")[0].strip() if os.getenv("GITHUB_TOKENS") else ""
    )
    if not token:
        return 0

    try:
        from github import Github
    except Exception:
        return 0

    gh = Github(token, per_page=100)
    unblocks = 0

    for review in reviews:
        repo_name = review.get("repo_name")
        pull_number = review.get("pull_number")
        created_at_raw = review.get("created_at")

        if not repo_name or not pull_number or not created_at_raw:
            continue

        review_dt = _safe_datetime(created_at_raw, datetime.now(timezone.utc))
        window_end = review_dt + timedelta(hours=review_window_hours)

        try:
            pr = gh.get_repo(str(repo_name)).get_pull(int(pull_number))
            commits = pr.get_commits()
            for commit in commits:
                commit_author = getattr(getattr(commit, "author", None), "login", None)
                if commit_author and commit_author.lower() == developer_username.lower():
                    continue

                commit_date = getattr(getattr(commit, "commit", None), "author", None)
                commit_dt = _safe_datetime(getattr(commit_date, "date", None), datetime.now(timezone.utc))

                if review_dt <= commit_dt <= window_end:
                    unblocks += 1
                    break
        except Exception:
            continue

    return unblocks


def _compute_glue_work(
    developer_username: str,
    week_start: Optional[Any] = None,
) -> Dict[str, float]:
    now_utc = datetime.now(timezone.utc)
    week_start_dt = _safe_datetime(week_start, now_utc - timedelta(days=7))

    reviews = github_fetcher.get_pr_reviews(developer_username, week_start_dt)

    review_comments_count = len(reviews)
    avg_words = (
        sum(_word_count(str(review.get("body", ""))) for review in reviews) / review_comments_count
        if review_comments_count
        else 0.0
    )

    review_depth = min(avg_words / 50.0, 1.0)
    unblock_signals = _count_unblock_signals(reviews, developer_username)
    unblock_component = min(unblock_signals / 5.0, 1.0)

    glue_score = (review_depth * 0.6) + (unblock_component * 0.4)

    return {
        "glue_score": max(min(glue_score, 1.0), 0.0),
        "review_comments_count": float(review_comments_count),
        "review_depth": review_depth,
        "unblock_signals": float(unblock_signals),
    }


def calculate_effort_score(
    *,
    repo_name: str,
    commit_sha: str,
    jira_context: str,
    developer_username: str,
    core_files: Optional[Iterable[str]] = None,
    commit_date: Optional[Any] = None,
    ticket_in_progress_date: Optional[Any] = None,
    old_coverage: float = 0.0,
    new_coverage: float = 0.0,
    week_start: Optional[Any] = None,
) -> Dict[str, Any]:
    diff_info = github_fetcher.get_diff(repo_name, commit_sha)
    relevance_info = _compute_relevance(diff_info.get("diff_text", ""), jira_context)

    if relevance_info.get("flag") == "needs_review":
        return {
            "score": 0.0,
            "confidence": "low",
            "flag": "needs_review",
            "breakdown": {
                "relevance": 0.0,
                "impact": 0.0,
                "complexity": 0.0,
                "glue_work": 0.0,
                "relevance_validation": relevance_info["validation"],
                "cosine_similarity": 0.0,
                "bm25_similarity": 0.0,
                "review_comments_count": 0,
                "review_depth": 0.0,
                "unblock_signals": 0,
            },
            "plain_english_explanation": relevance_info["plain_english"],
        }

    impact = _compute_impact(
        files_changed=int(diff_info.get("files_changed", 0) or 0),
        changed_files=diff_info.get("changed_files", []),
        core_files=core_files,
        old_coverage=float(old_coverage or 0.0),
        new_coverage=float(new_coverage or 0.0),
    )

    complexity = _compute_complexity(
        commit_date=commit_date,
        ticket_in_progress_date=ticket_in_progress_date,
        additions=int(diff_info.get("lines_added", 0) or 0),
        deletions=int(diff_info.get("lines_deleted", 0) or 0),
    )

    glue_info = _compute_glue_work(developer_username=developer_username, week_start=week_start)
    glue = glue_info["glue_score"]

    final_score = (relevance_info["relevance"] * 0.35 + impact * 0.25 + complexity * 0.20 + glue * 0.20) * 100.0

    result = {
        "score": round(max(min(final_score, 100.0), 0.0), 2),
        "confidence": relevance_info["confidence"],
        "breakdown": {
            "relevance": round(relevance_info["relevance"] * 100.0, 2),
            "impact": round(impact * 100.0, 2),
            "complexity": round(complexity * 100.0, 2),
            "glue_work": round(glue * 100.0, 2),
            "relevance_validation": relevance_info["validation"],
            "cosine_similarity": round(relevance_info["cosine"], 4),
            "bm25_similarity": round(relevance_info["bm25"], 4),
            "review_comments_count": int(glue_info["review_comments_count"]),
            "review_depth": round(glue_info["review_depth"], 4),
            "unblock_signals": int(glue_info["unblock_signals"]),
        },
        "plain_english_explanation": relevance_info["plain_english"],
    }

    if relevance_info.get("flag"):
        result["flag"] = relevance_info["flag"]

    return result


def score(
    diff_text: str,
    jira_context: str,
    developer: str,
    commit_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    metadata = commit_metadata or {}

    relevance_info = _compute_relevance(diff_text, jira_context)
    if relevance_info.get("flag") == "needs_review":
        return {
            "score": 0.0,
            "confidence": "low",
            "flag": "needs_review",
            "breakdown": {
                "relevance": 0.0,
                "impact": 0.0,
                "complexity": 0.0,
                "glue_work": 0.0,
                "relevance_validation": relevance_info["validation"],
                "cosine_similarity": 0.0,
                "bm25_similarity": 0.0,
                "review_comments_count": 0,
                "review_depth": 0.0,
                "unblock_signals": 0,
            },
            "plain_english_explanation": relevance_info["plain_english"],
        }

    impact = _compute_impact(
        files_changed=int(metadata.get("files_changed", 0) or 0),
        changed_files=metadata.get("changed_files", []),
        core_files=metadata.get("core_files", []),
        old_coverage=float(metadata.get("old_coverage", 0.0) or 0.0),
        new_coverage=float(metadata.get("new_coverage", 0.0) or 0.0),
    )

    complexity = _compute_complexity(
        commit_date=metadata.get("commit_date"),
        ticket_in_progress_date=metadata.get("ticket_in_progress_date"),
        additions=int(metadata.get("additions", 0) or 0),
        deletions=int(metadata.get("deletions", 0) or 0),
    )

    glue_info = _compute_glue_work(
        developer_username=developer,
        week_start=metadata.get("week_start"),
    )
    glue = glue_info["glue_score"]

    final_score = (relevance_info["relevance"] * 0.35 + impact * 0.25 + complexity * 0.20 + glue * 0.20) * 100.0

    result = {
        "score": round(max(min(final_score, 100.0), 0.0), 2),
        "confidence": relevance_info["confidence"],
        "breakdown": {
            "relevance": round(relevance_info["relevance"] * 100.0, 2),
            "impact": round(impact * 100.0, 2),
            "complexity": round(complexity * 100.0, 2),
            "glue_work": round(glue * 100.0, 2),
            "relevance_validation": relevance_info["validation"],
            "cosine_similarity": round(relevance_info["cosine"], 4),
            "bm25_similarity": round(relevance_info["bm25"], 4),
            "review_comments_count": int(glue_info["review_comments_count"]),
            "review_depth": round(glue_info["review_depth"], 4),
            "unblock_signals": int(glue_info["unblock_signals"]),
        },
        "plain_english_explanation": relevance_info["plain_english"],
    }

    if relevance_info.get("flag"):
        result["flag"] = relevance_info["flag"]

    return result
