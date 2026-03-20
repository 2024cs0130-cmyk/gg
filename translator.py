import re
from typing import List


def _summarize_paths(diff_text: str) -> str:
    paths: List[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            paths.append(line.replace("+++ b/", "", 1).strip())
    if not paths:
        return "multiple files"
    if len(paths) <= 3:
        return ", ".join(paths)
    return f"{', '.join(paths[:3])}, and {len(paths) - 3} more"


def diff_to_plain_english(diff_text: str) -> str:
    additions = sum(1 for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---"))
    files_hint = _summarize_paths(diff_text)

    keywords = {
        "test": r"\btest\b|\bpytest\b|\bunittest\b",
        "api": r"\bapi\b|\bendpoint\b|\broute\b",
        "db": r"\bsql\b|\bdatabase\b|\bmigration\b|\bmodel\b",
        "auth": r"\bauth\b|\btoken\b|\bpermission\b",
    }
    tags = [name for name, pattern in keywords.items() if re.search(pattern, diff_text, flags=re.IGNORECASE)]

    tag_text = f" Areas touched: {', '.join(tags)}." if tags else ""
    return (
        f"Updated {files_hint}. "
        f"The change adds about {additions} lines and removes about {deletions} lines."
        f"{tag_text}"
    ).strip()


def convert_diff_to_english(diff_text: str) -> str:
    return diff_to_plain_english(diff_text)


def translate_diff(diff_text: str) -> str:
    return diff_to_plain_english(diff_text)


def translate_diff_to_english(diff_text: str) -> str:
    return diff_to_plain_english(diff_text)
