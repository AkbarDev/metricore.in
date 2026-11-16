import json
import os
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.models import AITool

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Metricore.in - AI Directory & Platform",
    description="Curated AI platform tools directory with Paid vs Free alternatives and free-tier testing limits.",
    version="1.0.0",
)

# Static and Templates
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Data Loader
DATA_FILE = BASE_DIR / "data" / "tools.json"

def load_tools() -> List[AITool]:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [AITool(**item) for item in data]

def get_categories(tools: List[AITool]) -> List[str]:
    seen = []
    for tool in tools:
        if tool.category not in seen:
            seen.append(tool.category)
    return seen

# Web Routes
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    category: Optional[str] = None,
    pricing: Optional[str] = None,
    q: Optional[str] = None,
):
    all_tools = load_tools()
    categories = get_categories(all_tools)

    filtered = all_tools
    if category:
        filtered = [t for t in filtered if t.category.lower() == category.lower()]
    if pricing:
        filtered = [t for t in filtered if t.pricing_type.lower() == pricing.lower()]
    if q:
        query_str = q.lower()
        filtered = [
            t for t in filtered
            if query_str in t.name.lower()
            or query_str in t.description.lower()
            or query_str in t.category.lower()
            or query_str in t.free_tier_limit.lower()
        ]

    # Organize by category for comparison view
    category_pairs = []
    for cat in categories:
        cat_tools = [t for t in all_tools if t.category == cat]
        paid = next((t for t in cat_tools if t.pricing_type == "Paid"), None)
        free = next((t for t in cat_tools if t.pricing_type == "Free"), None)
        category_pairs.append({
            "category": cat,
            "paid": paid,
            "free": free
        })

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "tools": filtered,
            "categories": categories,
            "category_pairs": category_pairs,
            "active_category": category or "All",
            "active_pricing": pricing or "All",
            "search_query": q or "",
            "total_count": len(filtered),
        },
    )

@app.get("/tool/{tool_id}", response_class=HTMLResponse)
async def tool_detail(request: Request, tool_id: str):
    all_tools = load_tools()
    tool = next((t for t in all_tools if t.id == tool_id), None)
    if not tool:
        raise HTTPException(status_code=44, detail="Tool not found")

    alternative = None
    if tool.alternative_id:
        alternative = next((t for t in all_tools if t.id == tool.alternative_id), None)

    related = [t for t in all_tools if t.category == tool.category and t.id != tool.id]

    return templates.TemplateResponse(
        request=request,
        name="tool_detail.html",
        context={
            "tool": tool,
            "alternative": alternative,
            "related": related,
        },
    )

# HTMX Live Search Endpoint (Returns partial HTML of cards)
@app.get("/api/search", response_class=HTMLResponse)
async def live_search(
    request: Request,
    q: Optional[str] = "",
    category: Optional[str] = None,
    pricing: Optional[str] = None,
):
    all_tools = load_tools()
    filtered = all_tools

    if category and category != "All":
        filtered = [t for t in filtered if t.category.lower() == category.lower()]
    if pricing and pricing != "All":
        filtered = [t for t in filtered if t.pricing_type.lower() == pricing.lower()]
    if q:
        query_str = q.lower()
        filtered = [
            t for t in filtered
            if query_str in t.name.lower()
            or query_str in t.description.lower()
            or query_str in t.category.lower()
            or query_str in t.free_tier_limit.lower()
        ]

    return templates.TemplateResponse(
        request=request,
        name="components/tool_grid.html",
        context={
            "tools": filtered,
        },
    )

# REST API Endpoints
@app.get("/api/tools", response_model=List[AITool])
async def get_tools_api(
    category: Optional[str] = None,
    pricing: Optional[str] = None,
    q: Optional[str] = None,
):
    tools = load_tools()
    if category:
        tools = [t for t in tools if t.category.lower() == category.lower()]
    if pricing:
        tools = [t for t in tools if t.pricing_type.lower() == pricing.lower()]
    if q:
        query_str = q.lower()
        tools = [
            t for t in tools
            if query_str in t.name.lower()
            or query_str in t.description.lower()
            or query_str in t.category.lower()
        ]
    return tools

@app.get("/api/categories")
async def get_categories_api():
    tools = load_tools()
    return get_categories(tools)

