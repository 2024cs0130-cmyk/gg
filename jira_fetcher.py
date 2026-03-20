import json
import os
import re
from typing import Any, Dict, List

from jira import JIRA
from redis import Redis


class TicketTooVague(Exception):
    pass


JIRA_URL = os.getenv("JIRA_URL", "").strip()
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "").strip()
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "").strip()
REDIS_URL = os.getenv("REDIS_URL", "").strip()

if not JIRA_URL or not JIRA_EMAIL or not JIRA_API_TOKEN:
    raise RuntimeError("JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN environment variables are required")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL environment variable is required")

_redis = Redis.from_url(REDIS_URL, decode_responses=True)
_jira = JIRA(server=JIRA_URL, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))


def _flatten_adf_text(node: Any) -> str:
    if node is None:
        return ""

    if isinstance(node, str):
        return node

    if isinstance(node, list):
        return "\n".join(part for part in (_flatten_adf_text(item) for item in node) if part).strip()

    if isinstance(node, dict):
        text_parts: List[str] = []
        text_value = node.get("text")
        if isinstance(text_value, str) and text_value.strip():
            text_parts.append(text_value.strip())

        content = node.get("content")
        if isinstance(content, list):
            for child in content:
                child_text = _flatten_adf_text(child)
                if child_text:
                    text_parts.append(child_text)

        return "\n".join(text_parts).strip()

    return str(node)


def _extract_description(issue: Any) -> str:
    raw_description = getattr(issue.fields, "description", "")
    description = _flatten_adf_text(raw_description).strip()
    return description


def _resolve_epic_name(issue: Any) -> str:
    epic_key = getattr(issue.fields, "customfield_10014", None)
    if epic_key:
        try:
            epic_issue = _jira.issue(epic_key)
            return getattr(epic_issue.fields, "summary", str(epic_key))
        except Exception:
            return str(epic_key)

    parent = getattr(issue.fields, "parent", None)
    if parent is not None:
        try:
            parent_type = getattr(parent.fields.issuetype, "name", "")
            if parent_type.lower() == "epic":
                return getattr(parent.fields, "summary", "Unknown")
        except Exception:
            pass

    issue_type = getattr(issue.fields.issuetype, "name", "")
    if issue_type.lower() == "epic":
        return getattr(issue.fields, "summary", "Unknown")

    return "Unknown"


def ticket_quality_score(ticket: Dict[str, Any]) -> Dict[str, Any]:
    title = str(ticket.get("title") or "")
    description = str(ticket.get("description") or "")
    labels = ticket.get("labels") or []

    full_text = f"{title} {description}".strip()
    word_count = len(re.findall(r"\\b\\w+\\b", full_text))

    score = 0
    reasons: List[str] = []

    if word_count >= 80:
        score += 35
    elif word_count >= 40:
        score += 25
    elif word_count >= 20:
        score += 15
    else:
        score += 5
        reasons.append("description is too short")

    has_acceptance_criteria = bool(
        re.search(r"acceptance criteria|definition of done|done when", description, flags=re.IGNORECASE)
    )
    if has_acceptance_criteria:
        score += 25
    else:
        reasons.append("missing acceptance criteria")

    has_labels = len(labels) > 0
    if has_labels:
        score += 15
    else:
        reasons.append("missing labels")

    has_numbered_steps = bool(re.search(r"(^|\\n)\\s*\\d+[\\).:-]\\s+", description))
    if has_numbered_steps:
        score += 25
    else:
        reasons.append("missing numbered implementation or reproduction steps")

    if score < 40:
        rating = "INSUFFICIENT"
    elif score < 70:
        rating = "LOW"
    else:
        rating = "GOOD"

    reason_text = "; ".join(reasons) if reasons else "ticket has strong structure and context"
    return {
        "score": score,
        "rating": rating,
        "reason": f"Ticket quality is {rating} ({score}/100): {reason_text}",
    }


def get_ticket(ticket_id: str) -> Dict[str, Any]:
    cache_key = ticket_id
    cached = _redis.get(cache_key)
    if cached:
        return json.loads(cached)

    issue = _jira.issue(ticket_id)

    title = str(getattr(issue.fields, "summary", "") or "")
    description = _extract_description(issue)
    epic_name = _resolve_epic_name(issue)
    project_name = str(getattr(issue.fields.project, "name", "Unknown") or "Unknown")

    labels_raw = getattr(issue.fields, "labels", []) or []
    labels = [str(label) for label in labels_raw]

    priority_obj = getattr(issue.fields, "priority", None)
    priority = str(getattr(priority_obj, "name", "Unspecified") or "Unspecified")

    assignee_obj = getattr(issue.fields, "assignee", None)
    assignee = str(getattr(assignee_obj, "displayName", "Unassigned") or "Unassigned")

    domain = ", ".join(labels) if labels else "none"
    context = (
        f"Project: {project_name}\n"
        f"Epic: {epic_name}\n"
        f"Task: {title}\n"
        f"Details: {description}\n"
        f"Domain: {domain}"
    )

    ticket = {
        "ticket_id": ticket_id,
        "title": title,
        "description": description,
        "epic_name": epic_name,
        "project_name": project_name,
        "labels": labels,
        "priority": priority,
        "assignee": assignee,
        "context": context,
    }

    quality = ticket_quality_score(ticket)
    ticket["quality_score"] = quality["score"]
    ticket["quality_rating"] = quality["rating"]

    if quality["rating"] == "INSUFFICIENT":
        raise TicketTooVague(quality["reason"])

    _redis.setex(cache_key, 3600, json.dumps(ticket))
    return ticket
