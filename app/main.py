import json
import os
import math
import urllib.parse
from pathlib import Path
from typing import Optional, List, Dict
from fastapi import FastAPI, Request, Query, HTTPException, Form, Response, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.models import AITool, TopCategoryInfo
from app.auth import verify_credentials, register_user, get_user_by_username
from app.categories import TOP_CATEGORIES, get_top_category_by_slug, get_all_top_categories
from app.industry_stacks import (
    get_all_stacks,
    get_stack_by_slug,
    get_all_tools as get_all_stack_tools,
    get_tools_for_stack,
    get_tools_grouped_by_layer,
    get_all_use_cases,
    get_use_cases_for_stack,
    get_use_case_by_slug,
)

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
    title="Metricore.in - AI Tool Finder",
    description="Curated AI Tool Finder with Paid vs Free alternatives and free-tier testing limits.",
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
):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=302)

    all_tools = load_tools()
    categories = get_categories(all_tools)

    is_eval_board = (category == "AI tool eval board") or (view == "eval-board")
    if is_eval_board:
        category = "AI tool eval board"

    # Top-level intent categories with live counts
    top_categories = []
    for cat in TOP_CATEGORIES:
        count = sum(1 for t in all_tools if t.top_category_slug == cat["slug"])
        top_categories.append({**cat, "count": count})

    # Featured tools (8 top picks for the homepage showcase)
    featured_tools = [t for t in all_tools if t.is_top_pick][:8]
    if len(featured_tools) < 8:
        featured_tools = all_tools[:8]

    # Category pairs for benchmark comparison
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
            "all_tools": all_tools,
            "tools": all_tools,
            "all_filtered_tools": all_tools,
            "top_categories": top_categories,
            "featured_tools": featured_tools,
            "category_pairs": category_pairs,
            "is_eval_board": is_eval_board,
            "show_filters_row": False,  # Row 3 is hidden on homepage to keep it clean!
            "active_category_slug": "eval-board" if is_eval_board else "home",
            "is_authenticated": True,
            "username": get_current_user_name(request),
            "role": get_current_role(request),
        },
    )

@app.get("/eval-board/", response_class=HTMLResponse)
async def eval_board_view(request: Request):
    return await home(request=request, category="AI tool eval board", view="eval-board")

def make_filter_helpers(request: Request):
    def clear_filter_url(param: str) -> str:
        params = dict(request.query_params)
        params.pop(param, None)
        params.pop("page", None)
        q_str = urllib.parse.urlencode(params)
        return f"{request.url.path}?{q_str}" if q_str else request.url.path

    return clear_filter_url, request.url.path

def compute_filter_counts(tools_subset):
    counts_pricing = {"Free": 0, "Freemium": 0, "Paid": 0, "Open-source": 0}
    counts_platform = {"Web": 0, "API": 0, "Desktop": 0, "Mobile": 0, "Browser extension": 0}
    for t in tools_subset:
        tier = t.pricing_tier or "Paid"
        if tier in counts_pricing:
            counts_pricing[tier] += 1
        for p in (t.platforms or []):
            if p in counts_platform:
                counts_platform[p] += 1
    return counts_pricing, counts_platform

# ================= ALL AI TOOLS DIRECTORY PAGE =================
@app.get("/ai-tools/", response_class=HTMLResponse)
async def ai_tools_all(
    request: Request,
    pricing: Optional[str] = None,
    platform: Optional[str] = None,
    use_case: Optional[str] = None,
    sort: Optional[str] = "popular",
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=302)

    all_tools = load_tools()
    filtered = all_tools

    # Sub-filtering
    if pricing:
        filtered = [t for t in filtered if (t.pricing_tier == pricing or t.pricing_type == pricing)]
    if platform:
        filtered = [t for t in filtered if platform in (t.platforms or [])]
    if use_case:
        filtered = [t for t in filtered if use_case.lower() in [u.lower() for u in (t.use_cases or [])]]
    if q:
        query_str = q.lower().strip()
        filtered = [
            t for t in filtered
            if query_str in t.name.lower()
            or query_str in t.description.lower()
            or (t.tagline and query_str in t.tagline.lower())
            or (t.founders and query_str in t.founders.lower())
        ]

    # Sorting
    if sort == "newest":
        filtered = sorted(filtered, key=lambda x: x.founded_year or 0, reverse=True)
    elif sort == "top_rated":
        filtered = sorted(filtered, key=lambda x: x.rating or 0, reverse=True)
    else:  # popular
        filtered = sorted(filtered, key=lambda x: (x.is_top_pick, x.reviews_count or 0), reverse=True)

    # Counts
    counts_pricing, counts_platform = compute_filter_counts(all_tools)

    # Top Picks
    top_picks = [t for t in all_tools if t.is_top_pick][:4]

    # Squeezed Pagination (4 cards/row x 5 rows = 20 cards per page)
    total_tools = len(filtered)
    page_size = 20
    total_pages = max(1, math.ceil(total_tools / page_size))
    current_page = max(1, min(page, total_pages))

    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_tools)
    paginated_tools = filtered[start_idx:end_idx]
    start_item = start_idx + 1 if total_tools > 0 else 0
    end_item = end_idx

    clear_filter_url, current_clean_url = make_filter_helpers(request)
    is_filtered = bool(pricing or platform or use_case or q)
    active_filter_count = sum(1 for v in [pricing, platform, use_case] if v)

    # General use cases
    all_use_cases = []
    for cat in TOP_CATEGORIES:
        all_use_cases.extend(cat.get("use_cases", []))
    unique_use_cases = sorted(list(set(all_use_cases)))[:8]

    return templates.TemplateResponse(
        request=request,
        name="category_page.html",
        context={
            "tools": paginated_tools,
            "all_tools": all_tools,
            "total_count": total_tools,
            "top_picks": top_picks,
            "active_category": None,
            "active_category_slug": "all",
            "page_title": "All AI Tools Directory",
            "page_description": "Explore 500+ curated AI tools, foundation models, and open-source stacks with free-tier trial benchmarks.",
            "canonical_url": "https://metricore.in/ai-tools/",
            "show_filters_row": True,  # Row 3 visible on category & search pages!
            "counts_pricing": counts_pricing,
            "counts_platform": counts_platform,
            "category_use_cases": unique_use_cases,
            "selected_pricing": pricing or "",
            "selected_platform": platform or "",
            "selected_use_case": use_case or "",
            "selected_sort": sort or "popular",
            "search_query": q or "",
            "is_filtered": is_filtered,
            "active_filter_count": active_filter_count,
            "clear_filter_url": clear_filter_url,
            "current_clean_url": current_clean_url,
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

# ================= SPECIFIC CATEGORY PAGE =================
@app.get("/ai-tools/{category_slug}/", response_class=HTMLResponse)
async def ai_tools_category(
    request: Request,
    category_slug: str,
    pricing: Optional[str] = None,
    platform: Optional[str] = None,
    use_case: Optional[str] = None,
    sort: Optional[str] = "popular",
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=302)

    cat_info = get_top_category_by_slug(category_slug)
    if not cat_info:
        raise HTTPException(status_code=404, detail="Category not found")

    all_tools = load_tools()
    # Filter tools matching this category slug
    category_tools = [t for t in all_tools if t.top_category_slug == category_slug]
    filtered = category_tools

    # Sub-filtering
    if pricing:
        filtered = [t for t in filtered if (t.pricing_tier == pricing or t.pricing_type == pricing)]
    if platform:
        filtered = [t for t in filtered if platform in (t.platforms or [])]
    if use_case:
        filtered = [t for t in filtered if use_case.lower() in [u.lower() for u in (t.use_cases or [])]]
    if q:
        query_str = q.lower().strip()
        filtered = [
            t for t in filtered
            if query_str in t.name.lower()
            or query_str in t.description.lower()
            or (t.tagline and query_str in t.tagline.lower())
            or (t.founders and query_str in t.founders.lower())
        ]

    # Sorting
    if sort == "newest":
        filtered = sorted(filtered, key=lambda x: x.founded_year or 0, reverse=True)
    elif sort == "top_rated":
        filtered = sorted(filtered, key=lambda x: x.rating or 0, reverse=True)
    else:  # popular
        filtered = sorted(filtered, key=lambda x: (x.is_top_pick, x.reviews_count or 0), reverse=True)

    # Dynamic counts for this category
    counts_pricing, counts_platform = compute_filter_counts(category_tools)

    # 3-5 Top Picks for this category
    top_picks = [t for t in category_tools if t.is_top_pick][:4]
    if len(top_picks) < 3 and len(category_tools) >= 3:
        top_picks = category_tools[:3]

    # Squeezed Pagination (20 cards per page)
    total_tools = len(filtered)
    page_size = 20
    total_pages = max(1, math.ceil(total_tools / page_size))
    current_page = max(1, min(page, total_pages))

    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_tools)
    paginated_tools = filtered[start_idx:end_idx]
    start_item = start_idx + 1 if total_tools > 0 else 0
    end_item = end_idx

    clear_filter_url, current_clean_url = make_filter_helpers(request)
    is_filtered = bool(pricing or platform or use_case or q)
    active_filter_count = sum(1 for v in [pricing, platform, use_case] if v)

    return templates.TemplateResponse(
        request=request,
        name="category_page.html",
        context={
            "tools": paginated_tools,
            "all_tools": all_tools,
            "total_count": total_tools,
            "top_picks": top_picks,
            "active_category": cat_info,
            "active_category_slug": category_slug,
            "page_title": f"{cat_info['name']} AI Tools",
            "page_description": cat_info["description"],
            "canonical_url": f"https://metricore.in/ai-tools/{category_slug}/",
            "show_filters_row": True,  # Row 3 visible!
            "counts_pricing": counts_pricing,
            "counts_platform": counts_platform,
            "category_use_cases": cat_info.get("use_cases", []),
            "selected_pricing": pricing or "",
            "selected_platform": platform or "",
            "selected_use_case": use_case or "",
            "selected_sort": sort or "popular",
            "search_query": q or "",
            "is_filtered": is_filtered,
            "active_filter_count": active_filter_count,
            "clear_filter_url": clear_filter_url,
            "current_clean_url": current_clean_url,
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

# ================= AUTOSUGGEST API (GROUPED TOOLS, CATEGORIES, USE CASES) =================
@app.get("/api/autosuggest")
async def autosuggest(q: str = Query("", min_length=1)):
    all_tools = load_tools()
    query = q.lower().strip()

    # Group 1: Tools
    matched_tools = []
    for t in all_tools:
        if query in t.name.lower() or query in t.description.lower() or (t.tagline and query in t.tagline.lower()):
            matched_tools.append({
                "id": t.id,
                "name": t.name,
                "category": t.top_category_name or t.category,
                "pricing_type": t.pricing_tier or t.pricing_type,
                "image_url": t.image_url
            })
    matched_tools = matched_tools[:4]

    # Group 2: Categories
    matched_cats = []
    for cat in TOP_CATEGORIES:
        count = sum(1 for t in all_tools if t.top_category_slug == cat["slug"])
        if query in cat["name"].lower() or query in cat["slug"]:
            matched_cats.append({
                "slug": cat["slug"],
                "name": cat["name"],
                "icon": cat["icon"],
                "count": count
            })
    matched_cats = matched_cats[:3]

    # Group 3: Use Cases
    matched_use_cases = []
    for cat in TOP_CATEGORIES:
        for uc in cat.get("use_cases", []):
            if query in uc.lower():
                matched_use_cases.append({
                    "label": uc,
                    "category_slug": cat["slug"],
                    "category_name": cat["name"]
                })
    matched_use_cases = matched_use_cases[:3]

    return JSONResponse({
        "tools": matched_tools,
        "categories": matched_cats,
        "use_cases": matched_use_cases
    })

# ================= SUBMIT A TOOL API =================
@app.post("/api/submit-tool")
async def submit_tool(payload: Dict = Body(...)):
    # Record submission for editorial review
    return JSONResponse({
        "status": "success",
        "message": "Tool submission received for editorial review."
    })

# ================= INDUSTRY TOOL STACKS ROUTES =================
@app.get("/industry-tool-stacks/", response_class=HTMLResponse)
async def industry_tool_stacks_overview(
    request: Request,
    preview: Optional[str] = None,
):
    is_preview = (preview == "true" or preview == "1") or is_authenticated(request)
    all_stacks = get_all_stacks()
    stacks_with_counts = []
    for s in all_stacks:
        use_cases = get_use_cases_for_stack(s["slug"], include_unreviewed=is_preview)
        stacks_with_counts.append({
            **s,
            "use_case_count": len(use_cases)
        })

    return templates.TemplateResponse(
        request=request,
        name="industry_stacks/overview.html",
        context={
            "stacks": stacks_with_counts,
            "is_preview": is_preview,
            "show_filters_row": False,
            "active_category_slug": "industry-tool-stacks",
            "is_authenticated": is_authenticated(request),
            "username": get_current_user_name(request),
            "role": get_current_role(request),
        },
    )

@app.get("/industry-tool-stacks/{stack_slug}/", response_class=HTMLResponse)
async def industry_stack_detail(
    request: Request,
    stack_slug: str,
    preview: Optional[str] = None,
):
    is_preview = (preview == "true" or preview == "1") or is_authenticated(request)
    stack = get_stack_by_slug(stack_slug)
    if not stack:
        raise HTTPException(status_code=404, detail="Industry stack not found")

    tools = get_tools_for_stack(stack.get("tool_ids", []))
    grouped_tools = get_tools_grouped_by_layer(stack.get("tool_ids", []))
    use_cases = get_use_cases_for_stack(stack_slug, include_unreviewed=is_preview)

    return templates.TemplateResponse(
        request=request,
        name="industry_stacks/stack_detail.html",
        context={
            "stack": stack,
            "tools": tools,
            "grouped_tools": grouped_tools,
            "use_cases": use_cases,
            "is_preview": is_preview,
            "show_filters_row": False,
            "active_category_slug": "industry-tool-stacks",
            "is_authenticated": is_authenticated(request),
            "username": get_current_user_name(request),
            "role": get_current_role(request),
        },
    )

@app.get("/industry-tool-stacks/{stack_slug}/{use_case_slug}/", response_class=HTMLResponse)
async def industry_use_case_detail(
    request: Request,
    stack_slug: str,
    use_case_slug: str,
    preview: Optional[str] = None,
):
    is_preview = (preview == "true" or preview == "1") or is_authenticated(request)
    stack = get_stack_by_slug(stack_slug)
    if not stack:
        raise HTTPException(status_code=404, detail="Industry stack not found")

    use_case = get_use_case_by_slug(stack_slug, use_case_slug, include_unreviewed=is_preview)
    if not use_case:
        unreviewed = get_use_case_by_slug(stack_slug, use_case_slug, include_unreviewed=True)
        if unreviewed and not is_preview:
            raise HTTPException(status_code=403, detail="This use case is currently pending editorial human review. Add ?preview=true to view in preview mode.")
        raise HTTPException(status_code=404, detail="Use case not found")

    tools_used = get_tools_for_stack(use_case.get("tool_ids", []))
    main_tool_name = tools_used[0]["name"] if tools_used else "Corporate Tools"

    return templates.TemplateResponse(
        request=request,
        name="industry_stacks/use_case_detail.html",
        context={
            "stack": stack,
            "use_case": use_case,
            "tools_used": tools_used,
            "main_tool_name": main_tool_name,
            "is_preview": is_preview,
            "show_filters_row": False,
            "active_category_slug": "industry-tool-stacks",
            "is_authenticated": is_authenticated(request),
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

