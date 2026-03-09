import json
import os
import re
from core.constants import REF_TIER1_SCORE, REF_TIER2_SCORE, REF_TIER3_SCORE, REF_TIER3_MIN_KEYWORDS


def extract_file_paths(text: str) -> set[str]:
    return set(re.findall(r"[\w\-./\\]+\.\w+", text))


def normalize_paths(paths: set[str], project_root: str = "") -> set[str]:
    """Normalize paths to relative form for consistent matching.

    Strips project_root prefix and leading slashes so both
    '/home/user/project/src/auth.ts' and 'src/auth.ts' become 'src/auth.ts'.
    """
    normalized = set()
    for p in paths:
        if project_root and p.startswith(project_root):
            p = p[len(project_root):].lstrip("/\\")
        normalized.add(p)
    return normalized


def extract_directories(paths: set[str]) -> set[str]:
    return {os.path.dirname(p) for p in paths if os.path.dirname(p)}

def extract_keywords(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"\w+", text) if len(w) >= 4}

def score_entries_against_content(entries: list[dict], content: str, project_root: str = "") -> dict[int, int]:
    content_paths = normalize_paths(extract_file_paths(content), project_root)
    content_dirs = extract_directories(content_paths)
    content_keywords = extract_keywords(content)
    scores = {}

    for i, entry in enumerate(entries):
        score = 0
        entry_text = entry.get("title", "") + " " + entry.get("body", "")
        entry_paths = normalize_paths(extract_file_paths(entry_text), project_root)
        entry_dirs = extract_directories(entry_paths)
        entry_keywords = extract_keywords(entry_text)

        if entry_paths & content_paths:
            score += REF_TIER1_SCORE
        elif entry_dirs & content_dirs:
            score += REF_TIER2_SCORE

        keyword_overlap = entry_keywords & content_keywords
        if len(keyword_overlap) >= REF_TIER3_MIN_KEYWORDS:
            score += REF_TIER3_SCORE

        scores[i] = score

    return scores


def load_ref_cache(cache_path: str) -> dict:
    try:
        with open(cache_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_ref_cache(cache_path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(data, f)


def apply_ref_cache(entries: list[dict], cache: dict) -> list[dict]:
    """Apply accumulated ref scores from cache to entries."""
    for key, count in cache.items():
        try:
            idx = int(key)
            count = int(count)
        except (ValueError, TypeError):
            continue
        if 0 <= idx < len(entries):
            entries[idx]["ref"] = entries[idx].get("ref", 0) + count
    return entries
