import json
import os
import math
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Request, Query, HTTPException, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.models import AITool
from app.auth import verify_credentials, register_user, get_user_by_username

BASE_DIR = Path(__file__).resolve().parent

AUTH_COOKIE_NAME = "metricore_auth"
USER_COOKIE_NAME = "metricore_user"
ROLE_COOKIE_NAME = "metricore_role"

def is_authenticated(request: Request) -> bool:
    return request.cookies.get(AUTH_COOKIE_NAME) == "authenticated"

def get_current_user_name(request: Request) -> str:
    return request.cookies.get(USER_COOKIE_NAME) or "Member"

def get_current_role(request: Request) -> str:
    return request.cookies.get(ROLE_COOKIE_NAME) or "user"

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
@app.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    error: Optional[str] = None,
    success: Optional[str] = None,
    tab: Optional[str] = "login"
):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": error,
            "success": success,
            "is_authenticated": is_authenticated(request),
            "username": get_current_user_name(request),
            "active_tab": tab or "login",
        },
    )

@app.post("/login", response_class=HTMLResponse)
async def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    user = verify_credentials(username, password)
    if user:
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key=AUTH_COOKIE_NAME,
            value="authenticated",
            max_age=60 * 60 * 24 * 7,  # 7 days
            httponly=True,
            samesite="lax",
        )
        response.set_cookie(
            key=USER_COOKIE_NAME,
            value=user["username"],
            max_age=60 * 60 * 24 * 7,
            httponly=True,
            samesite="lax",
        )
        response.set_cookie(
            key=ROLE_COOKIE_NAME,
            value=user.get("role", "user"),
            max_age=60 * 60 * 24 * 7,
            httponly=True,
            samesite="lax",
        )
        return response

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": "Invalid username or password. Don't have an account? Click 'Create an Account' below to register.",
            "is_authenticated": False,
            "entered_username": username,
            "active_tab": "login",
        },
        status_code=401,
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "is_authenticated": is_authenticated(request),
            "username": get_current_user_name(request),
            "active_tab": "register",
        },
    )

@app.post("/register", response_class=HTMLResponse)
async def handle_register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    success, msg = register_user(username=username, email=email, password=password)
    if success:
        # Automatic login after successful registration
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key=AUTH_COOKIE_NAME,
            value="authenticated",
            max_age=60 * 60 * 24 * 7,
            httponly=True,
            samesite="lax",
        )
        response.set_cookie(
            key=USER_COOKIE_NAME,
            value=username.strip(),
            max_age=60 * 60 * 24 * 7,
            httponly=True,
            samesite="lax",
        )
        response.set_cookie(
            key=ROLE_COOKIE_NAME,
            value="user",
            max_age=60 * 60 * 24 * 7,
            httponly=True,
            samesite="lax",
        )
        return response

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": msg,
            "is_authenticated": False,
            "entered_username": username,
            "entered_email": email,
            "active_tab": "register",
        },
        status_code=400,
    )

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key=AUTH_COOKIE_NAME)
    response.delete_cookie(key=USER_COOKIE_NAME)
    response.delete_cookie(key=ROLE_COOKIE_NAME)
    return response

@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    category: Optional[str] = None,
    pricing: Optional[str] = None,
    q: Optional[str] = None,
    view: Optional[str] = None,
    page: int = Query(1, ge=1),
):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=302)

    all_tools = load_tools()
    categories = get_categories(all_tools)
    modalities = sorted(list(set(t.modality_type for t in all_tools if t.modality_type)))

    is_eval_board = (category == "AI tool eval board") or (view == "eval-board")
    if is_eval_board:
        category = "AI tool eval board"

    filtered = all_tools
    if category and category != "AI tool eval board" and category != "All":
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
            or (t.founders and query_str in t.founders.lower())
            or (t.country_name and query_str in t.country_name.lower())
        ]

    # Benchmark-grade pagination (4 cards per row x 5 rows = 20 cards per page)
    total_tools = len(filtered)
    page_size = 20
    total_pages = max(1, math.ceil(total_tools / page_size))
    current_page = max(1, min(page, total_pages))

    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_tools)
    paginated_tools = filtered[start_idx:end_idx]
    start_item = start_idx + 1 if total_tools > 0 else 0
    end_item = end_idx

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
            "tools": paginated_tools,
            "all_filtered_tools": filtered,
            "all_tools": all_tools,
            "categories": categories,
            "modalities": modalities,
            "category_pairs": category_pairs,
            "active_category": category or "All",
            "active_pricing": pricing or "All",
            "search_query": q or "",
            "is_eval_board": is_eval_board,
            "total_count": total_tools,
            "current_page": current_page,
            "total_pages": total_pages,
            "page_size": page_size,
            "start_item": start_item,
            "end_item": end_item,
            "is_authenticated": True,
            "username": get_current_user_name(request),
            "role": get_current_role(request),
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

# HTMX Live Search Endpoint (Returns partial HTML of cards with pagination support)
@app.get("/api/search", response_class=HTMLResponse)
async def live_search(
    request: Request,
    q: Optional[str] = "",
    category: Optional[str] = None,
    pricing: Optional[str] = None,
    page: int = 1,
):
    all_tools = load_tools()
    filtered = all_tools

    if category and category != "All" and category != "AI tool eval board":
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
            or (t.founders and query_str in t.founders.lower())
            or (t.country_name and query_str in t.country_name.lower())
        ]

    total_tools = len(filtered)
    page_size = 20
    total_pages = max(1, math.ceil(total_tools / page_size))
    current_page = max(1, min(page, total_pages))

    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_tools)
    paginated_tools = filtered[start_idx:end_idx]
    start_item = start_idx + 1 if total_tools > 0 else 0
    end_item = end_idx

    return templates.TemplateResponse(
        request=request,
        name="components/tool_grid.html",
        context={
            "tools": paginated_tools,
            "total_count": total_tools,
            "current_page": current_page,
            "total_pages": total_pages,
            "page_size": page_size,
            "start_item": start_item,
            "end_item": end_item,
            "active_category": category or "All",
            "active_pricing": pricing or "All",
            "search_query": q or "",
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

