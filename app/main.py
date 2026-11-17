import json
import os
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
):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=302)

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

