"""
Google AI Stack Data Access Layer for Metricore.
Loads and manages curated Google AI tools, media assets, and competitor comparisons
from app/data/google_stack.json.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

DATA_PATH = Path(__file__).resolve().parent / "data" / "google_stack.json"


def _read_data() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        return {"tools": [], "metadata": {}}
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"tools": [], "metadata": {}}


def get_google_stack_metadata() -> Dict[str, Any]:
    data = _read_data()
    return data.get("metadata", {})


def get_google_competitor_matrix() -> List[Dict[str, Any]]:
    data = _read_data()
    return data.get("competitor_matrix", [])


def get_all_google_tools() -> List[Dict[str, Any]]:
    data = _read_data()
    return data.get("tools", [])


def get_google_tool_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    tools = get_all_google_tools()
    for tool in tools:
        if tool.get("slug") == slug or tool.get("id") == slug:
            return tool
    return None


def get_google_categories() -> List[Dict[str, Any]]:
    """
    Returns unique categories found in Google AI Stack with counts and icons.
    Categories match user specification:
    assistant, research, image, video, marketing, app and UI building, coding
    """
    tools = get_all_google_tools()
    counts: Dict[str, int] = {}
    for tool in tools:
        cat = tool.get("category", "other")
        counts[cat] = counts.get(cat, 0) + 1

    category_meta = {
        "coding": {"label": "Coding", "icon": "💻", "order": 1},
        "app and UI building": {"label": "App & UI Building", "icon": "🎨", "order": 2},
        "research": {"label": "Research", "icon": "📚", "order": 3},
        "marketing": {"label": "Marketing", "icon": "📢", "order": 4},
        "image": {"label": "Image", "icon": "🖼️", "order": 5},
        "video": {"label": "Video", "icon": "🎬", "order": 6},
        "assistant": {"label": "Assistant", "icon": "✨", "order": 7},
    }

    result = []
    for slug, meta in sorted(category_meta.items(), key=lambda x: x[1]["order"]):
        count = counts.get(slug, 0)
        if count > 0:
            result.append({
                "slug": slug,
                "label": meta["label"],
                "icon": meta["icon"],
                "count": count
            })
    return result


def get_google_status_counts() -> Dict[str, int]:
    tools = get_all_google_tools()
    counts = {"all": len(tools), "free": 0, "freemium": 0, "preview": 0}
    for tool in tools:
        badge = tool.get("pricing_badge", "").lower()
        if "freemium" in badge:
            counts["freemium"] += 1
        elif "preview" in badge:
            counts["preview"] += 1
        else:
            counts["free"] += 1
    return counts

