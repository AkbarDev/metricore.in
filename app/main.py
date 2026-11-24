import json
import os
import math
import time
import urllib.parse
from collections import defaultdict
from pathlib import Path
from typing import Optional, List, Dict, Set
from fastapi import FastAPI, Request, Query, HTTPException, Body, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, HttpUrl

from app.models import AITool, PublicAITool, TopCategoryInfo
from app.categories import (
    TOP_CATEGORIES,
    get_top_category_by_slug,
    get_all_top_categories,
    get_shared_categories,
    get_grouped_shared_categories,
)
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
from app.google_stack import (
    get_all_google_tools,
    get_google_tool_by_slug,
    get_google_categories,
    get_google_status_counts,
    get_google_stack_metadata,
    get_google_competitor_matrix,
)

BASE_DIR = Path(__file__).resolve().parent

# ================= FASTAPI APP INITIALIZATION =================
app = FastAPI(
    title="Metricore.in - AI Tool Finder",
    description="Curated AI Tool Finder with Paid vs Free alternatives and free-tier testing limits.",
    version="1.0.0",
    debug=False,
)

# Static files (Mounted strictly to app/static and google_stack)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/google_stack", StaticFiles(directory=BASE_DIR.parent / "google_stack"), name="google_stack")

# Templates with autoescaping
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.autoescape = True
templates.env.globals["get_grouped_categories"] = get_grouped_shared_categories
templates.env.globals["get_shared_categories"] = get_shared_categories

# Data Loader
DATA_FILE = BASE_DIR / "data" / "tools.json"

def sanitize_tool_for_public(tool: AITool) -> AITool:
    """Mask fields not permitted on the public site per editorial & non-commercial policy."""
    # 2. Hide rating and reviews_count everywhere on the public site
    tool.rating = None
    tool.reviews_count = None
    # 4. Hide eval_compliance and eval_license_risk from the public site for now
    tool.eval_compliance = None
    tool.eval_license_risk = None
    # 5. Hide founders and total_funding everywhere unless facts_source_url exists
    # Apply the same rule to founded_year, country_name, and github_stars: show only when sourced
    if not tool.facts_source_url:
        tool.founders = None
        tool.total_funding = None
        tool.founded_year = None
        tool.country_name = None
        tool.country_flag = None
        tool.github_stars = None
    return tool

def load_tools() -> List[AITool]:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [sanitize_tool_for_public(AITool(**item)) for item in data]

def get_categories(tools: List[AITool]) -> List[str]:
    seen = []
    for tool in tools:
        if tool.category not in seen:
            seen.append(tool.category)
    return seen

# ================= ALLOWLISTS & VALIDATION CONSTANTS =================
ALLOWED_SORTS: Set[str] = {"popular", "newest", "name_asc", "top_rated"}
ALLOWED_PRICINGS: Set[str] = {"", "Free", "Freemium", "Paid", "Open-source"}
ALLOWED_PLATFORMS: Set[str] = {"", "Web", "API", "Desktop", "Mobile", "Browser extension"}
ALLOWED_SEARCH_TYPES: Set[str] = {"tools", "stacks"}

def get_allowed_category_slugs() -> Set[str]:
    cats = get_shared_categories()
    slugs = {c["slug"] for c in cats}
    slugs.add("all")
    return slugs

def validate_q(q: Optional[str]) -> str:
    if not q:
        return ""
    q_clean = q.strip()
    if len(q_clean) > 100:
        raise HTTPException(status_code=400, detail="Search query must be 100 characters or fewer.")
    return q_clean

def validate_page(page: int) -> int:
    if page < 1 or page > 1000:
        raise HTTPException(status_code=400, detail="Page parameter must be between 1 and 1000.")
    return page

# ================= DRAFT / UNREVIEWED CONTENT PREVIEW CONTROL =================
def is_preview_enabled(request: Request) -> bool:
    """
    Draft / unreviewed content preview:
    Only enabled locally when METRICORE_PREVIEW=1 is set in the environment
    AND ?preview=true or ?preview=1 is passed in query parameters.
    Without METRICORE_PREVIEW=1, ?preview=true does nothing and unreviewed items are never visible.

    HOW TO APPROVE CONTENT FOR PRODUCTION:
    Set `"needs_human_review": false` in `app/data/industry_stacks.json` (or tools.json) and commit.
    """
    if os.environ.get("METRICORE_PREVIEW") == "1":
        preview = request.query_params.get("preview", "").lower()
        return preview in ("true", "1")
    return False

# ================= IN-MEMORY RATE LIMITER & CLIENT IP LOGIC =================
import ipaddress
from collections import OrderedDict, deque

class InMemoryRateLimiter:
    """
    In-memory rate limiter using sliding-window deques, LRU key eviction, and periodic expiration.
    NOTE: Rate limits are in-memory and tracked per process.
    """
    def __init__(
        self,
        max_keys: int = 10000,
        cleanup_interval_seconds: int = 60,
        cleanup_call_frequency: int = 100
    ):
        self._requests: OrderedDict[str, deque] = OrderedDict()
        self.max_keys = max_keys
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self.cleanup_call_frequency = cleanup_call_frequency
        self._call_counter = 0
        self._last_cleanup = time.time()

    def check_and_record(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """
        Check rate limit and record timestamp only if allowed.
        Returns: (is_allowed, retry_after_seconds)
        """
        now = time.time()
        self._call_counter += 1

        # Periodic cleanup of expired entries
        if self._call_counter >= self.cleanup_call_frequency or (now - self._last_cleanup >= self.cleanup_interval_seconds):
            self.cleanup(now, window_seconds)

        cutoff = now - window_seconds
        q = self._requests.get(key)
        if q is not None:
            # Purge timestamps outside the sliding window
            while q and q[0] <= cutoff:
                q.popleft()
            self._requests.move_to_end(key)
        else:
            # Enforce max tracked keys cap by evicting oldest key
            while len(self._requests) >= self.max_keys:
                self._requests.popitem(last=False)
            q = deque()
            self._requests[key] = q

        if len(q) >= max_requests:
            # Request is BLOCKED: do NOT append timestamp. Compute retry-after.
            oldest_ts = q[0]
            retry_after = max(1, math.ceil((oldest_ts + window_seconds) - now))
            return False, retry_after

        # Request is ALLOWED: record current timestamp
        q.append(now)
        return True, 0

    def cleanup(self, now: Optional[float] = None, default_window: int = 3600):
        """Removes expired entries and deletes empty keys across all tracked entries."""
        if now is None:
            now = time.time()
        self._last_cleanup = now
        self._call_counter = 0

        cutoff = now - default_window
        empty_keys = []
        for k, q in list(self._requests.items()):
            while q and q[0] <= cutoff:
                q.popleft()
            if not q:
                empty_keys.append(k)

        for k in empty_keys:
            self._requests.pop(k, None)

rate_limiter = InMemoryRateLimiter()

def is_trusted_peer(host: Optional[str]) -> bool:
    """Returns True if host is loopback, private or link-local address."""
    if not host:
        return False
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_loopback or ip.is_private or ip.is_link_local
    except ValueError:
        return False

def get_client_ip(request: Request) -> str:
    """
    Determines client IP address safely:
    - Default: request.client.host (direct connecting address)
    - Trusts X-Forwarded-For ONLY when request.client.host is loopback, private or link-local (a proxy)
    - In that case, uses rightmost address in X-Forwarded-For (respecting optional METRICORE_TRUSTED_PROXY_HOPS)
    - Validates with ipaddress.ip_address(); if invalid, falls back to request.client.host
    """
    peer_host = request.client.host if request.client and request.client.host else "127.0.0.1"

    if is_trusted_peer(peer_host):
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ips = [p.strip() for p in forwarded.split(",") if p.strip()]
            if ips:
                try:
                    hops = int(os.environ.get("METRICORE_TRUSTED_PROXY_HOPS", "1"))
                except ValueError:
                    hops = 1
                if hops < 1:
                    hops = 1

                index = -hops if len(ips) >= hops else 0
                candidate = ips[index]
                try:
                    valid_ip = ipaddress.ip_address(candidate)
                    return str(valid_ip)
                except ValueError:
                    pass

    return peer_host

# ================= SECURITY HEADERS & HEAD REQUEST MIDDLEWARE =================
@app.middleware("http")
async def head_request_middleware(request: Request, call_next):
    if request.method == "HEAD":
        request.scope["method"] = "GET"
        try:
            response = await call_next(request)
        finally:
            request.scope["method"] = "HEAD"
        return Response(status_code=response.status_code, headers=dict(response.headers))
    return await call_next(request)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-Frame-Options"] = "DENY"

    # Strict-Transport-Security: trust x-forwarded-proto ONLY when direct peer is a trusted proxy
    peer_host = request.client.host if request.client and request.client.host else "127.0.0.1"
    is_https = request.url.scheme == "https"
    if is_trusted_peer(peer_host):
        if request.headers.get("x-forwarded-proto", "").lower() == "https":
            is_https = True

    if is_https:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Content-Security-Policy: tightened to self-hosted assets with external script CDNs removed.
    # Note: 'unsafe-inline' is retained for scripts because inline application scripts exist in templates.
    # Future improvement: implement cryptographic request nonces (e.g. 'nonce-{random}') to replace 'unsafe-inline'.
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: https:",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

    return response

# ================= CUSTOM ERROR HANDLERS (404, 500) =================
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="404.html",
        status_code=404,
        context={"request": request},
    )

@app.exception_handler(500)
async def custom_500_handler(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="500.html",
        status_code=500,
        context={"request": request},
    )

# ================= PYDANTIC SUBMIT-TOOL MODEL =================
class SubmitToolRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    website_url: HttpUrl
    category: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    pricing_type: Optional[str] = Field("Free", max_length=30)
    honeypot: Optional[str] = Field(None, max_length=50)

# ================= HELPER FUNCTIONS =================
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

# ================= WEB ROUTES =================

# 1. HOME PAGE (Public, no login redirect)
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    category: Optional[str] = None,
    pricing: Optional[str] = None,
    q: Optional[str] = None,
    view: Optional[str] = None,
):
    query_str = validate_q(q)
    if pricing and pricing not in ALLOWED_PRICINGS:
        raise HTTPException(status_code=400, detail="Invalid pricing filter value.")

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

    # Featured tools (8 top picks for homepage showcase)
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
            "show_filters_row": False,
            "active_category_slug": "eval-board" if is_eval_board else "home",
        },
    )

@app.get("/eval-board/", response_class=HTMLResponse)
async def eval_board_view(request: Request):
    return await home(request=request, category="AI tool eval board", view="eval-board")

# 2. ALL AI TOOLS DIRECTORY PAGE (Public)
@app.get("/ai-tools/", response_class=HTMLResponse)
async def ai_tools_all(
    request: Request,
    pricing: Optional[str] = None,
    platform: Optional[str] = None,
    use_case: Optional[str] = None,
    sort: Optional[str] = "popular",
    q: Optional[str] = None,
    page: int = Query(1),
):
    query_str = validate_q(q)
    page_num = validate_page(page)

    if pricing and pricing not in ALLOWED_PRICINGS:
        raise HTTPException(status_code=400, detail="Invalid pricing filter value.")
    if platform and platform not in ALLOWED_PLATFORMS:
        raise HTTPException(status_code=400, detail="Invalid platform filter value.")
    if sort and sort not in ALLOWED_SORTS:
        raise HTTPException(status_code=400, detail="Invalid sort parameter.")
    if use_case and len(use_case) > 100:
        raise HTTPException(status_code=400, detail="Use case parameter too long.")

    all_tools = load_tools()
    filtered = all_tools

    if pricing:
        filtered = [t for t in filtered if (t.pricing_tier == pricing or t.pricing_type == pricing)]
    if platform:
        filtered = [t for t in filtered if platform in (t.platforms or [])]
    if use_case:
        filtered = [t for t in filtered if use_case.lower() in [u.lower() for u in (t.use_cases or [])]]
    if query_str:
        q_lower = query_str.lower()
        filtered = [
            t for t in filtered
            if q_lower in t.name.lower()
            or q_lower in t.description.lower()
            or (t.tagline and q_lower in t.tagline.lower())
            or (t.founders and q_lower in t.founders.lower())
        ]

    # Sorting (Neutral options; rating and reviews_count hidden)
    if sort == "newest":
        filtered = sorted(filtered, key=lambda x: (x.founded_year or 0, (x.name or "").lower()), reverse=True)
    elif sort == "name_asc" or sort == "top_rated":
        filtered = sorted(filtered, key=lambda x: (x.name or "").lower())
    else:  # popular / default
        filtered = sorted(filtered, key=lambda x: (not x.is_top_pick, (x.name or "").lower()))

    counts_pricing, counts_platform = compute_filter_counts(all_tools)
    top_picks = [t for t in all_tools if t.is_top_pick][:4]

    total_tools = len(filtered)
    page_size = 20
    total_pages = max(1, math.ceil(total_tools / page_size))
    current_page = max(1, min(page_num, total_pages))

    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_tools)
    paginated_tools = filtered[start_idx:end_idx]
    start_item = start_idx + 1 if total_tools > 0 else 0
    end_item = end_idx

    clear_filter_url, current_clean_url = make_filter_helpers(request)
    is_filtered = bool(pricing or platform or use_case or query_str)
    active_filter_count = sum(1 for v in [pricing, platform, use_case] if v)

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
            "show_filters_row": True,
            "counts_pricing": counts_pricing,
            "counts_platform": counts_platform,
            "category_use_cases": unique_use_cases,
            "selected_pricing": pricing or "",
            "selected_platform": platform or "",
            "selected_use_case": use_case or "",
            "selected_sort": sort or "popular",
            "search_query": query_str,
            "is_filtered": is_filtered,
            "active_filter_count": active_filter_count,
            "clear_filter_url": clear_filter_url,
            "current_clean_url": current_clean_url,
            "current_page": current_page,
            "total_pages": total_pages,
            "page_size": page_size,
            "start_item": start_item,
            "end_item": end_item,
        },
    )

# 3. SPECIFIC CATEGORY PAGE (Public)
@app.get("/ai-tools/{category_slug}/", response_class=HTMLResponse)
async def ai_tools_category(
    request: Request,
    category_slug: str,
    pricing: Optional[str] = None,
    platform: Optional[str] = None,
    use_case: Optional[str] = None,
    sort: Optional[str] = "popular",
    q: Optional[str] = None,
    page: int = Query(1),
):
    query_str = validate_q(q)
    page_num = validate_page(page)

    cat_info = get_top_category_by_slug(category_slug)
    if not cat_info:
        raise HTTPException(status_code=404, detail="Category not found")

    if pricing and pricing not in ALLOWED_PRICINGS:
        raise HTTPException(status_code=400, detail="Invalid pricing filter value.")
    if platform and platform not in ALLOWED_PLATFORMS:
        raise HTTPException(status_code=400, detail="Invalid platform filter value.")
    if sort and sort not in ALLOWED_SORTS:
        raise HTTPException(status_code=400, detail="Invalid sort parameter.")

    all_tools = load_tools()
    category_tools = [t for t in all_tools if t.top_category_slug == category_slug]
    filtered = category_tools

    if pricing:
        filtered = [t for t in filtered if (t.pricing_tier == pricing or t.pricing_type == pricing)]
    if platform:
        filtered = [t for t in filtered if platform in (t.platforms or [])]
    if use_case:
        filtered = [t for t in filtered if use_case.lower() in [u.lower() for u in (t.use_cases or [])]]
    if query_str:
        q_lower = query_str.lower()
        filtered = [
            t for t in filtered
            if q_lower in t.name.lower()
            or q_lower in t.description.lower()
            or (t.tagline and q_lower in t.tagline.lower())
            or (t.founders and q_lower in t.founders.lower())
        ]

    if sort == "newest":
        filtered = sorted(filtered, key=lambda x: (x.founded_year or 0, (x.name or "").lower()), reverse=True)
    elif sort == "name_asc" or sort == "top_rated":
        filtered = sorted(filtered, key=lambda x: (x.name or "").lower())
    else:  # popular / default
        filtered = sorted(filtered, key=lambda x: (not x.is_top_pick, (x.name or "").lower()))

    counts_pricing, counts_platform = compute_filter_counts(category_tools)
    top_picks = [t for t in category_tools if t.is_top_pick][:4]
    if len(top_picks) < 3 and len(category_tools) >= 3:
        top_picks = category_tools[:3]

    total_tools = len(filtered)
    page_size = 20
    total_pages = max(1, math.ceil(total_tools / page_size))
    current_page = max(1, min(page_num, total_pages))

    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_tools)
    paginated_tools = filtered[start_idx:end_idx]
    start_item = start_idx + 1 if total_tools > 0 else 0
    end_item = end_idx

    clear_filter_url, current_clean_url = make_filter_helpers(request)
    is_filtered = bool(pricing or platform or use_case or query_str)
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
            "show_filters_row": True,
            "counts_pricing": counts_pricing,
            "counts_platform": counts_platform,
            "category_use_cases": cat_info.get("use_cases", []),
            "selected_pricing": pricing or "",
            "selected_platform": platform or "",
            "selected_use_case": use_case or "",
            "selected_sort": sort or "popular",
            "search_query": query_str,
            "is_filtered": is_filtered,
            "active_filter_count": active_filter_count,
            "clear_filter_url": clear_filter_url,
            "current_clean_url": current_clean_url,
            "current_page": current_page,
            "total_pages": total_pages,
            "page_size": page_size,
            "start_item": start_item,
            "end_item": end_item,
        },
    )

# 4. SHARED CATEGORIES API
@app.get("/api/categories")
async def get_categories_api():
    grouped = get_grouped_shared_categories(refresh=False)
    return JSONResponse(grouped)

# 5. AUTOSUGGEST API (Rate limited: 60 req/min per IP, max 100 char query)
@app.get("/api/autosuggest")
async def autosuggest(
    request: Request,
    q: str = Query("", max_length=100),
    cat: Optional[str] = "all",
    type: Optional[str] = "tools"
):
    # Global route-group backstop (600 req/min across all callers)
    allowed, retry_after = rate_limiter.check_and_record("global:search_group", max_requests=600, window_seconds=60)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Service busy. Please retry shortly."},
            headers={"Retry-After": str(retry_after)}
        )

    # Per-IP rate limit (60 req/min per client IP)
    client_ip = get_client_ip(request)
    allowed, retry_after = rate_limiter.check_and_record(f"search_ip:{client_ip}", max_requests=60, window_seconds=60)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please wait a minute."},
            headers={"Retry-After": str(retry_after)}
        )

    query = validate_q(q).lower()
    cat_slug = (cat or "all").strip()
    search_type = type if type in ALLOWED_SEARCH_TYPES else "tools"

    if search_type == "stacks":
        stacks = get_all_stacks()
        use_cases = get_all_use_cases(include_unreviewed=is_preview_enabled(request))

        matched_stacks = []
        for s in stacks:
            if query in s["name"].lower() or query in s["summary"].lower() or query in s["function"].lower():
                matched_stacks.append({
                    "id": s["slug"],
                    "name": s["name"],
                    "category": s["function"],
                    "pricing_type": f"{len(s['tool_ids'])} Tools",
                    "url": f"/industry-tool-stacks/{s['slug']}/"
                })
        matched_stacks = matched_stacks[:5]

        matched_ucs = []
        for uc in use_cases:
            if query in uc["title"].lower() or query in uc["situation"].lower() or query in uc["role"].lower():
                matched_ucs.append({
                    "label": uc["title"],
                    "category_slug": uc["stack_slug"],
                    "category_name": uc["role"],
                    "url": f"/industry-tool-stacks/{uc['stack_slug']}/{uc['slug']}/"
                })
        matched_ucs = matched_ucs[:5]

        matched_cats = []
        for s in stacks:
            if query in s["function"].lower():
                matched_cats.append({
                    "slug": s["slug"],
                    "name": s["function"],
                    "icon": s.get("icon", "💼"),
                    "count": len(s["tool_ids"]),
                    "url": f"/industry-tool-stacks/{s['slug']}/"
                })
        matched_cats = matched_cats[:5]

        return JSONResponse({
            "tools": matched_stacks,
            "categories": matched_cats,
            "use_cases": matched_ucs
        })

    # Default Tools Mode
    all_tools = load_tools()
    candidate_tools = all_tools
    if cat_slug and cat_slug != "all":
        candidate_tools = [
            t for t in all_tools
            if t.top_category_slug == cat_slug or cat_slug.lower() in (t.category or "").lower()
        ]

    matched_tools = []
    for t in candidate_tools:
        if (
            query in t.name.lower()
            or query in t.description.lower()
            or (t.tagline and query in t.tagline.lower())
            or (t.founders and query in t.founders.lower())
        ):
            matched_tools.append({
                "id": t.id,
                "name": t.name,
                "category": t.top_category_name or t.category,
                "pricing_type": t.pricing_tier or t.pricing_type,
                "image_url": t.image_url,
                "url": f"/tool/{t.id}"
            })
    matched_tools = matched_tools[:5]

    matched_cats = []
    shared_cats = get_shared_categories()
    for c in shared_cats:
        if query in c["label"].lower() or query in c["slug"]:
            matched_cats.append({
                "slug": c["slug"],
                "name": c["label"],
                "icon": c["icon"],
                "count": c["tool_count"],
                "url": f"/ai-tools/{c['slug']}/"
            })
    matched_cats = matched_cats[:5]

    matched_use_cases = []
    for c in shared_cats:
        for uc in c.get("use_cases", []):
            if query in uc.lower():
                matched_use_cases.append({
                    "label": uc,
                    "category_slug": c["slug"],
                    "category_name": c["label"],
                    "url": f"/search?q={urllib.parse.quote(uc)}&cat={c['slug']}&type=tools"
                })
    matched_use_cases = matched_use_cases[:5]

    return JSONResponse({
        "tools": matched_tools,
        "categories": matched_cats,
        "use_cases": matched_use_cases
    })

# 6. SCOPED SEARCH ROUTE (/search?q=...&cat=...&type=...)
@app.get("/search", response_class=HTMLResponse)
async def search_page(
    request: Request,
    q: Optional[str] = "",
    cat: Optional[str] = "all",
    type: Optional[str] = "tools"
):
    query_str = validate_q(q)
    cat_slug = (cat or "all").strip()
    search_type = "stacks" if type == "stacks" else "tools"

    # Category validation against allowlist
    allowed_slugs = get_allowed_category_slugs()
    if cat_slug not in allowed_slugs and cat_slug != "all":
        cat_slug = "all"

    # Resolve active category info
    active_category = {"slug": "all", "label": "All categories", "icon": "⚡"}
    if cat_slug and cat_slug != "all":
        shared_cats = get_shared_categories()
        match = next((c for c in shared_cats if c["slug"] == cat_slug), None)
        if match:
            active_category = match
        else:
            active_category = {"slug": cat_slug, "label": cat_slug.replace("-", " ").title(), "icon": "📁"}

    if search_type == "stacks":
        all_stacks = get_all_stacks()
        all_ucs = get_all_use_cases(include_unreviewed=is_preview_enabled(request))

        matched_stacks = all_stacks
        matched_ucs = all_ucs

        if cat_slug and cat_slug != "all":
            matched_stacks = [s for s in matched_stacks if s["slug"] == cat_slug or s.get("function", "").lower() == active_category["label"].lower()]
            matched_ucs = [u for u in matched_ucs if u["stack_slug"] == cat_slug or (matched_stacks and u["stack_slug"] == matched_stacks[0]["slug"])]

        if query_str:
            q_lower = query_str.lower()
            matched_stacks = [
                s for s in matched_stacks
                if q_lower in s["name"].lower()
                or q_lower in s["summary"].lower()
                or q_lower in s.get("description", "").lower()
                or any(q_lower in tid for tid in s.get("tool_ids", []))
            ]
            matched_ucs = [
                u for u in matched_ucs
                if q_lower in u["title"].lower()
                or q_lower in u["situation"].lower()
                or q_lower in u.get("role", "").lower()
                or any(q_lower in tid for tid in u.get("tool_ids", []))
            ]

        total_results = len(matched_stacks) + len(matched_ucs)
        return templates.TemplateResponse(
            request=request,
            name="search_results.html",
            context={
                "query": query_str,
                "active_category": active_category,
                "search_type": "stacks",
                "stacks": matched_stacks,
                "use_cases": matched_ucs,
                "total_results": total_results,
            }
        )

    # Search Type: AI Tools
    all_tools = load_tools()
    filtered = all_tools

    if cat_slug and cat_slug != "all":
        filtered = [
            t for t in filtered
            if t.top_category_slug == cat_slug or cat_slug.lower() in (t.category or "").lower()
        ]

    if query_str:
        q_lower = query_str.lower()
        filtered = [
            t for t in filtered
            if q_lower in t.name.lower()
            or q_lower in t.description.lower()
            or (t.tagline and q_lower in t.tagline.lower())
            or (t.founders and q_lower in t.founders.lower())
            or (t.country_name and q_lower in t.country_name.lower())
            or any(q_lower in u.lower() for u in (t.use_cases or []))
            or any(q_lower in tag.lower() for tag in (t.tags or []))
        ]

    total_results = len(filtered)
    return templates.TemplateResponse(
        request=request,
        name="search_results.html",
        context={
            "query": query_str,
            "active_category": active_category,
            "search_type": "tools",
            "tools": filtered,
            "total_results": total_results,
        }
    )

# 7. SUBMIT A TOOL API (Pydantic model, 10KB cap, honeypot, rate limited 5/hr)
@app.post("/api/submit-tool")
async def submit_tool(request: Request, payload: SubmitToolRequest):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 10240:
        raise HTTPException(status_code=413, detail="Payload too large. Maximum size is 10KB.")

    # Global route-group backstop (60 submissions/hour across all callers)
    allowed, retry_after = rate_limiter.check_and_record("global:submit_group", max_requests=60, window_seconds=3600)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Submission queue busy. Please retry later."},
            headers={"Retry-After": str(retry_after)}
        )

    # Per-IP rate limit (5 submissions/hour per client IP)
    client_ip = get_client_ip(request)
    allowed, retry_after = rate_limiter.check_and_record(f"submit_ip:{client_ip}", max_requests=5, window_seconds=3600)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many submissions. Please try again later."},
            headers={"Retry-After": str(retry_after)}
        )

    # Bot honeypot check
    if payload.honeypot:
        return JSONResponse(status_code=400, content={"detail": "Invalid submission."})

    # Record submission for editorial review
    return JSONResponse({
        "status": "success",
        "message": "Tool submission received for editorial review."
    })

# 8. INDUSTRY TOOL STACKS ROUTES (Public)
@app.get("/industry-tool-stacks/", response_class=HTMLResponse)
async def industry_tool_stacks_overview(
    request: Request,
    preview: Optional[str] = None,
):
    is_preview = is_preview_enabled(request)
    all_stacks = get_all_stacks()
    stacks_with_counts = []
    for s in all_stacks:
        use_cases = get_use_cases_for_stack(s["slug"], include_unreviewed=is_preview)
        stacks_with_counts.append({
            **s,
            "use_case_count": len(use_cases),
            "tool_count": len(s.get("tool_ids", []))
        })

    total_tools_count = len(get_all_stack_tools())
    total_departments_count = len(all_stacks)
    total_workflows_count = sum(s["use_case_count"] for s in stacks_with_counts)

    return templates.TemplateResponse(
        request=request,
        name="industry_stacks/overview.html",
        context={
            "stacks": stacks_with_counts,
            "total_tools_count": total_tools_count,
            "total_departments_count": total_departments_count,
            "total_workflows_count": total_workflows_count,
            "is_preview": is_preview,
            "show_filters_row": False,
            "active_category_slug": "industry-tool-stacks",
        },
    )

@app.get("/industry-tool-stacks/{stack_slug}/", response_class=HTMLResponse)
async def industry_stack_detail(
    request: Request,
    stack_slug: str,
    preview: Optional[str] = None,
):
    is_preview = is_preview_enabled(request)
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
        },
    )

@app.get("/industry-tool-stacks/{stack_slug}/{use_case_slug}/", response_class=HTMLResponse)
async def industry_use_case_detail(
    request: Request,
    stack_slug: str,
    use_case_slug: str,
    preview: Optional[str] = None,
):
    is_preview = is_preview_enabled(request)
    stack = get_stack_by_slug(stack_slug)
    if not stack:
        raise HTTPException(status_code=404, detail="Industry stack not found")

    use_case = get_use_case_by_slug(stack_slug, use_case_slug, include_unreviewed=is_preview)
    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")

    tools_used = get_tools_for_stack(use_case.get("tool_ids", []))
    main_tool_name = tools_used[0]["name"] if tools_used else "Industry Tools"

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
        },
    )

# ================= GOOGLE AI STACK ROUTES =================
@app.get("/google-ai-stack/", response_class=HTMLResponse)
async def google_ai_stack_overview(
    request: Request,
    category: Optional[str] = None,
    pricing: Optional[str] = None,
    q: Optional[str] = None,
):
    tools = get_all_google_tools()
    categories = get_google_categories()
    status_counts = get_google_status_counts()
    metadata = get_google_stack_metadata()

    return templates.TemplateResponse(
        request=request,
        name="google_stack/index.html",
        context={
            "tools": tools,
            "categories": categories,
            "status_counts": status_counts,
            "metadata": metadata,
            "competitor_matrix": get_google_competitor_matrix(),
            "selected_category": category,
            "selected_pricing": pricing,
            "search_query": q or "",
        },
    )

@app.get("/google-ai-stack/{tool_slug}/", response_class=HTMLResponse)
async def google_ai_tool_detail(request: Request, tool_slug: str):
    tool = get_google_tool_by_slug(tool_slug)
    if not tool:
        raise HTTPException(status_code=404, detail="Google AI Tool not found")

    all_tools = get_all_google_tools()
    related_tools = [t for t in all_tools if t.get("id") != tool.get("id") and t.get("category") == tool.get("category")][:3]
    if len(related_tools) < 3:
        for t in all_tools:
            if t.get("id") != tool.get("id") and t not in related_tools:
                related_tools.append(t)
            if len(related_tools) == 3:
                break

    return templates.TemplateResponse(
        request=request,
        name="google_stack/detail.html",
        context={
            "tool": tool,
            "related_tools": related_tools,
            "metadata": get_google_stack_metadata(),
        },
    )

# 9. TOOL DETAIL PAGE (Public)
@app.get("/tool/{tool_id}", response_class=HTMLResponse)
async def tool_detail(request: Request, tool_id: str):
    all_tools = load_tools()
    tool = next((t for t in all_tools if t.id == tool_id), None)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

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

# 10. HTMX LIVE SEARCH ENDPOINT (Rate limited: 60 req/min)
@app.get("/api/search", response_class=HTMLResponse)
async def live_search(
    request: Request,
    q: Optional[str] = "",
    category: Optional[str] = None,
    pricing: Optional[str] = None,
    page: int = 1,
):
    # Global route-group backstop (600 req/min across all callers)
    allowed, retry_after = rate_limiter.check_and_record("global:search_group", max_requests=600, window_seconds=60)
    if not allowed:
        return HTMLResponse(
            status_code=429,
            content=f"<div class='p-4 text-rose-400'>Service busy. Please retry in {retry_after} seconds.</div>",
            headers={"Retry-After": str(retry_after)}
        )

    # Per-IP rate limit (60 req/min per client IP)
    client_ip = get_client_ip(request)
    allowed, retry_after = rate_limiter.check_and_record(f"search_ip:{client_ip}", max_requests=60, window_seconds=60)
    if not allowed:
        return HTMLResponse(
            status_code=429,
            content=f"<div class='p-4 text-rose-400'>Too many requests. Please retry in {retry_after} seconds.</div>",
            headers={"Retry-After": str(retry_after)}
        )

    query_str = validate_q(q)
    page_num = validate_page(page)

    all_tools = load_tools()
    filtered = all_tools

    if category and category != "All" and category != "AI tool eval board":
        filtered = [t for t in filtered if t.category.lower() == category.lower()]
    if pricing and pricing != "All" and pricing in ALLOWED_PRICINGS:
        filtered = [t for t in filtered if t.pricing_type.lower() == pricing.lower()]
    if query_str:
        q_lower = query_str.lower()
        filtered = [
            t for t in filtered
            if q_lower in t.name.lower()
            or q_lower in t.description.lower()
            or q_lower in t.category.lower()
            or q_lower in t.free_tier_limit.lower()
            or (t.founders and q_lower in t.founders.lower())
            or (t.country_name and q_lower in t.country_name.lower())
        ]

    total_tools = len(filtered)
    page_size = 20
    total_pages = max(1, math.ceil(total_tools / page_size))
    current_page = max(1, min(page_num, total_pages))

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
            "search_query": query_str,
        },
    )

# 11. REST API TOOLS ENDPOINT (Public schema strictly omitting hidden fields)
@app.get("/api/tools", response_model=List[PublicAITool])
async def get_tools_api(
    category: Optional[str] = None,
    pricing: Optional[str] = None,
    q: Optional[str] = None,
):
    query_str = validate_q(q)
    tools = load_tools()
    if category:
        tools = [t for t in tools if t.category.lower() == category.lower()]
    if pricing and pricing in ALLOWED_PRICINGS:
        tools = [t for t in tools if t.pricing_type.lower() == pricing.lower()]
    if query_str:
        q_lower = query_str.lower()
        tools = [
            t for t in tools
            if q_lower in t.name.lower()
            or q_lower in t.description.lower()
            or q_lower in t.category.lower()
        ]
    return tools

# 12. TRANSPARENCY, POLICY & METHODOLOGY ROUTES (Public)
@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    return templates.TemplateResponse(request=request, name="privacy.html")

@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    return templates.TemplateResponse(request=request, name="terms.html")

@app.get("/corrections", response_class=HTMLResponse)
async def corrections_page(request: Request):
    return templates.TemplateResponse(request=request, name="corrections.html")

@app.get("/methodology", response_class=HTMLResponse)
async def methodology_page(request: Request):
    return templates.TemplateResponse(request=request, name="methodology.html")

