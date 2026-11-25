"""
GitHub Repos Data Access Layer for Metricore.
Loads and manages curated open-source GitHub repositories from app/data/github_repo.json.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

DATA_PATH = Path(__file__).resolve().parent / "data" / "github_repo.json"


def _read_data() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        return {"repos": [], "metadata": {}}
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"repos": [], "metadata": {}}


def get_github_repo_metadata() -> Dict[str, Any]:
    return _read_data().get("metadata", {})


def get_all_github_repos() -> List[Dict[str, Any]]:
    return _read_data().get("repos", [])


def get_featured_github_repos() -> List[Dict[str, Any]]:
    return [r for r in get_all_github_repos() if r.get("featured")]


def get_github_repo_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    for repo in get_all_github_repos():
        if repo.get("slug") == slug or repo.get("id") == slug:
            return repo
    return None


def get_github_categories() -> List[Dict[str, Any]]:
    repos = get_all_github_repos()
    counts: Dict[str, int] = {}
    for r in repos:
        cat = r.get("category", "Other")
        counts[cat] = counts.get(cat, 0) + 1

    icons = {
        "AI Agents": "🤖",
        "Web & Search": "🌐",
        "AI Companions & Voice": "🎭",
        "Workflow & Email": "📬",
        "Audio & Voice": "🎙️",
        "AI Chat & Interfaces": "💬",
        "Image & Cinema": "🎬",
    }
    return [
        {"slug": cat, "label": cat, "icon": icons.get(cat, "📦"), "count": count}
        for cat, count in counts.items()
    ]


def get_github_languages() -> List[str]:
    langs = []
    for r in get_all_github_repos():
        lang = r.get("language")
        if lang and lang not in langs:
            langs.append(lang)
    return langs


def get_github_licenses() -> List[str]:
    licenses = []
    for r in get_all_github_repos():
        lic = r.get("license")
        if lic and lic not in licenses:
            licenses.append(lic)
    return licenses
