"""
Metricore Shared Category Architecture & Taxonomies
Unifies categories across AI Tool Finder and Industry Tool Stacks.
Provides automated dynamic counts for tools and stacks.
"""

from pathlib import Path
from typing import Dict, List, Optional
import json

DATA_DIR = Path(__file__).resolve().parent / "data"
TOOLS_FILE = DATA_DIR / "tools.json"
STACKS_FILE = DATA_DIR / "industry_stacks.json"

# Master Taxonomy Definitions
TAXONOMY_DEFINITIONS: List[Dict] = [
    # ================= DEPARTMENTS =================
    {
        "slug": "marketing-seo",
        "label": "Marketing",
        "icon": "🚀",
        "group": "department",
        "parent": None,
        "sort_order": 1,
        "description": "Cross-channel campaign platforms, SEO auditing, social intelligence & ad creatives.",
        "use_cases": ["Ad creatives", "Social media scheduling", "SEO optimization", "Campaign copy"],
        "stack_function": "Marketing",
    },
    {
        "slug": "data-analytics",
        "label": "Data & Analytics",
        "icon": "📊",
        "group": "department",
        "parent": None,
        "sort_order": 2,
        "description": "Enterprise BI dashboards, SQL modeling, automated metrics & statistical forecasting.",
        "use_cases": ["Data visualization", "Automated reporting", "SQL generation", "Spreadsheet analysis"],
        "stack_function": "Data & Analytics",
    },
    {
        "slug": "finance-accounting",
        "label": "Finance & Accounting",
        "icon": "💳",
        "group": "department",
        "parent": None,
        "sort_order": 3,
        "description": "FP&A scenario planning, autonomous invoice matching, general ledger coding & compliance.",
        "use_cases": ["Financial modeling", "Invoice processing", "Budget forecasting", "SEC reporting", "Spreadsheet formulas"],
        "stack_function": "Finance & Accounting",
    },
    {
        "slug": "hr-recruiting",
        "label": "HR & Recruiting",
        "icon": "👥",
        "group": "department",
        "parent": None,
        "sort_order": 4,
        "description": "Talent graph matching, structured video screening, inclusive job drafting & employee onboarding.",
        "use_cases": ["Candidate sourcing", "Video interviews", "Performance reviews", "Employee onboarding", "Job descriptions"],
        "stack_function": "Human Resources",
    },
    {
        "slug": "customer-support",
        "label": "Customer Support",
        "icon": "🎧",
        "group": "department",
        "parent": None,
        "sort_order": 5,
        "description": "Omnichannel ticketing, automated resolution chatbots, knowledge bases & SLA triage.",
        "use_cases": ["Support chatbots", "Ticket routing", "Agent assistance", "Helpdesk automation", "Sentiment analysis"],
        "stack_function": "Customer Support",
    },
    {
        "slug": "business-sales",
        "label": "Sales & Outreach",
        "icon": "💼",
        "group": "department",
        "parent": None,
        "sort_order": 6,
        "description": "B2B lead intelligence, call coaching transcription, email scoring & pipeline management.",
        "use_cases": ["Sales outreach", "CRM enrichment", "Pitch decks", "Client onboarding"],
        "stack_function": "Sales & Outreach",
    },
    {
        "slug": "productivity-automation",
        "label": "Operations & Admin",
        "icon": "⚡",
        "group": "department",
        "parent": None,
        "sort_order": 7,
        "description": "Task orchestration, team wikis, relational operational databases & automated triggers.",
        "use_cases": ["Workflow automation", "Website builders", "AI presentations", "Task routing"],
        "stack_function": "Product & Operations",
    },
    {
        "slug": "legal-compliance",
        "label": "Legal & Compliance",
        "icon": "⚖️",
        "group": "department",
        "parent": None,
        "sort_order": 8,
        "description": "Contract redlining, MSA risk analysis, clause playbooks & regulatory auditing.",
        "use_cases": ["Contract review", "Due diligence", "Legal research", "Regulatory compliance", "Contract drafting"],
        "stack_function": "Legal & Compliance",
    },
    {
        "slug": "code-dev",
        "label": "Product & Engineering",
        "icon": "💻",
        "group": "department",
        "parent": None,
        "sort_order": 9,
        "description": "AI code completion, automated debugging, API testing & developer sprint tracking.",
        "use_cases": ["Code autocompletion", "Multi-file coding", "Code refactoring", "Bug fixing", "CLI automation"],
        "stack_function": "Product & Operations",
    },

    # ================= TOOL TYPES =================
    {
        "slug": "writing-content",
        "label": "Writing & Content",
        "icon": "✍️",
        "group": "tool_type",
        "parent": None,
        "sort_order": 10,
        "description": "AI writing assistants, long-form content creators, copywriting tools, and grammar paraphrasers.",
        "use_cases": ["Copywriting", "Long-form articles", "Grammar & Editing", "Blog posts", "Email drafting"],
    },
    {
        "slug": "image-design",
        "label": "Image & Design",
        "icon": "🎨",
        "group": "tool_type",
        "parent": None,
        "sort_order": 11,
        "description": "Generative image synthesis, vector art, UI design, thumbnail creators, and photo editors.",
        "use_cases": ["Text-to-image", "Background removal", "Photo editing", "UI/UX design", "Vector art", "Thumbnails"],
    },
    {
        "slug": "video-animation",
        "label": "Video & Animation",
        "icon": "🎬",
        "group": "tool_type",
        "parent": None,
        "sort_order": 12,
        "description": "Cinematic text-to-video, AI spokespersons, video editing, and dynamic motion graphics.",
        "use_cases": ["Text-to-video", "AI avatars", "Video editing", "Cinematic effects", "Captions & subtitles"],
    },
    {
        "slug": "audio-voice",
        "label": "Audio & Voice",
        "icon": "🎙️",
        "group": "tool_type",
        "parent": None,
        "sort_order": 13,
        "description": "Realistic voice cloning, text-to-speech, AI music generation, and audio stem separation.",
        "use_cases": ["Voice cloning", "Text-to-speech", "Music composition", "Audio stems", "Podcasting"],
    },
    {
        "slug": "code-dev",
        "label": "Code & Development",
        "icon": "💻",
        "group": "tool_type",
        "parent": None,
        "sort_order": 14,
        "description": "Autonomous coding agents, AI IDEs, code generation, and developer workflow automation.",
        "use_cases": ["Code autocompletion", "Multi-file coding", "Code refactoring", "Bug fixing", "CLI automation"],
    },
    {
        "slug": "research-chat",
        "label": "Research & Chat Assistants",
        "icon": "🔍",
        "group": "tool_type",
        "parent": None,
        "sort_order": 15,
        "description": "Frontier reasoning engines, conversational search, academic paper synthesis, and web-grounded research.",
        "use_cases": ["Academic synthesis", "Web-grounded search", "Frontier reasoning", "Document Q&A"],
    },
    {
        "slug": "education",
        "label": "Education & Learning",
        "icon": "🎓",
        "group": "tool_type",
        "parent": None,
        "sort_order": 16,
        "description": "Personalized AI study tutors, academic consensus finders, research paraphrasers, and learning aids.",
        "use_cases": ["Academic citations", "Study summaries", "Flashcards", "Concept explanation"],
    },
    {
        "slug": "agents-workflows",
        "label": "Agents & Workflows",
        "icon": "🤖",
        "group": "tool_type",
        "parent": None,
        "sort_order": 17,
        "description": "Autonomous multi-agent loops, chatbot orchestrators, computer-use agents, and background workers.",
        "use_cases": ["Autonomous agents", "Support chatbots", "API orchestration", "Computer-use loops"],
    },
    {
        "slug": "productivity-automation",
        "label": "Automation Engines",
        "icon": "⚡",
        "group": "tool_type",
        "parent": None,
        "sort_order": 18,
        "description": "Workflow automation engines, AI web builders, presentation makers, and productivity tools.",
        "use_cases": ["Workflow automation", "Website builders", "AI presentations", "Task routing"],
    },
]

# Legacy / Backward compatibility format
TOP_CATEGORIES = [
    {
        "slug": item["slug"],
        "name": item["label"],
        "icon": item["icon"],
        "description": item["description"],
        "use_cases": item["use_cases"],
        "group": item["group"],
    }
    for item in TAXONOMY_DEFINITIONS
]

TOP_CATEGORIES_BY_SLUG = {cat["slug"]: cat for cat in TOP_CATEGORIES}

def get_top_category_by_slug(slug: str) -> Optional[Dict]:
    return TOP_CATEGORIES_BY_SLUG.get(slug)

def get_all_top_categories() -> List[Dict]:
    return TOP_CATEGORIES

# Dynamic Shared Category Cache
_cached_shared_categories: Optional[List[Dict]] = None

def get_shared_categories(refresh: bool = False) -> List[Dict]:
    """
    Computes live tool_count and stack_count for each category across tools.json and industry_stacks.json.
    Excludes entries where tool_count == 0.
    """
    global _cached_shared_categories
    if _cached_shared_categories and not refresh:
        return _cached_shared_categories

    tool_counts: Dict[str, int] = {}
    if TOOLS_FILE.exists():
        try:
            with open(TOOLS_FILE, "r", encoding="utf-8") as f:
                tools_data = json.load(f)
                for t in tools_data:
                    c_slug = t.get("top_category_slug")
                    if c_slug:
                        tool_counts[c_slug] = tool_counts.get(c_slug, 0) + 1
        except Exception as e:
            print(f"Error reading tools for category counts: {e}")

    stack_counts: Dict[str, int] = {}
    if STACKS_FILE.exists():
        try:
            with open(STACKS_FILE, "r", encoding="utf-8") as f:
                stacks_data = json.load(f)
                for s in stacks_data.get("stacks", []):
                    fn = s.get("function")
                    if fn:
                        stack_counts[fn] = len(s.get("tool_ids", []))
        except Exception as e:
            print(f"Error reading stacks for category counts: {e}")

    enriched = []
    for item in TAXONOMY_DEFINITIONS:
        slug = item["slug"]
        t_count = tool_counts.get(slug, 0)
        s_fn = item.get("stack_function")
        s_count = stack_counts.get(s_fn, 0) if s_fn else 0

        # Acceptance requirement: Hide entries with zero tools
        if t_count == 0 and s_count == 0:
            continue

        enriched.append({
            "slug": slug,
            "label": item["label"],
            "icon": item["icon"],
            "group": item["group"],
            "parent": item.get("parent"),
            "tool_count": t_count,
            "stack_count": s_count,
            "sort_order": item["sort_order"],
            "description": item["description"],
            "use_cases": item["use_cases"],
        })

    enriched.sort(key=lambda x: (x["group"] != "department", x["sort_order"]))
    _cached_shared_categories = enriched
    return enriched

def get_grouped_shared_categories(refresh: bool = False) -> Dict[str, List[Dict]]:
    categories = get_shared_categories(refresh=refresh)
    departments = [c for c in categories if c["group"] == "department"]
    tool_types = [c for c in categories if c["group"] == "tool_type"]
    return {
        "departments": departments,
        "tool_types": tool_types,
    }
