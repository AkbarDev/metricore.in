import json
from pathlib import Path
from typing import List, Dict, Optional, Any

DATA_PATH = Path(__file__).resolve().parent / "data" / "industry_stacks.json"

def load_data() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        return {"stacks": [], "tools": [], "use_cases": []}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_all_stacks() -> List[Dict[str, Any]]:
    data = load_data()
    return data.get("stacks", [])

def get_stack_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    for s in get_all_stacks():
        if s.get("slug") == slug:
            return s
    return None

def get_all_tools() -> List[Dict[str, Any]]:
    data = load_data()
    return data.get("tools", [])

def get_tool_by_id(tool_id: str) -> Optional[Dict[str, Any]]:
    for t in get_all_tools():
        if t.get("id") == tool_id:
            return t
    return None

def get_tools_for_stack(tool_ids: List[str]) -> List[Dict[str, Any]]:
    all_tools = {t["id"]: t for t in get_all_tools()}
    return [all_tools[tid] for tid in tool_ids if tid in all_tools]

def get_tools_grouped_by_layer(tool_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    tools = get_tools_for_stack(tool_ids)
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for t in tools:
        layer = t.get("layer", "Other Tools")
        if layer not in grouped:
            grouped[layer] = []
        grouped[layer].append(t)
    return grouped

def get_all_use_cases(include_unreviewed: bool = False) -> List[Dict[str, Any]]:
    data = load_data()
    cases = data.get("use_cases", [])
    if include_unreviewed:
        return cases
    return [c for c in cases if not c.get("needs_human_review", False)]

def get_use_cases_for_stack(stack_slug: str, include_unreviewed: bool = False) -> List[Dict[str, Any]]:
    cases = get_all_use_cases(include_unreviewed=include_unreviewed)
    return [c for c in cases if c.get("stack_slug") == stack_slug]

def get_use_case_by_slug(stack_slug: str, use_case_slug: str, include_unreviewed: bool = False) -> Optional[Dict[str, Any]]:
    cases = get_all_use_cases(include_unreviewed=include_unreviewed)
    for c in cases:
        if c.get("stack_slug") == stack_slug and c.get("slug") == use_case_slug:
            return c
    return None
