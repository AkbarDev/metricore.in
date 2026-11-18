"""
Metricore Top-Level Category Architecture & Taxonomies
Groups tools by visitor intent rather than underlying raw technology.
"""

from typing import Dict, List

TOP_CATEGORIES: List[Dict] = [
    {
        "slug": "writing-content",
        "name": "Writing & Content",
        "icon": "✍️",
        "description": "AI writing assistants, long-form content creators, copywriting tools, and grammar paraphrasers.",
        "use_cases": ["Copywriting", "Long-form articles", "Grammar & Editing", "Blog posts", "Email drafting"],
        "legacy_categories": ["AI Writing Assistant"]
    },
    {
        "slug": "image-design",
        "name": "Image & Design",
        "icon": "🎨",
        "description": "Generative image synthesis, vector art, UI design, thumbnail creators, and photo editors.",
        "use_cases": ["Text-to-image", "Background removal", "Photo editing", "UI/UX design", "Vector art", "Thumbnails"],
        "legacy_categories": ["Image Creation", "Thumbnail / Image Editing", "Design & UI", "Presentation Maker"]
    },
    {
        "slug": "video-animation",
        "name": "Video & Animation",
        "icon": "🎬",
        "description": "Cinematic text-to-video, AI spokespersons, video editing, and dynamic motion graphics.",
        "use_cases": ["Text-to-video", "AI avatars", "Video editing", "Cinematic effects", "Captions & subtitles"],
        "legacy_categories": ["Video Generation", "Cinematic Creation", "Avatar Creation"]
    },
    {
        "slug": "audio-voice",
        "name": "Audio & Voice",
        "icon": "🎙️",
        "description": "Realistic voice cloning, text-to-speech, AI music generation, and audio stem separation.",
        "use_cases": ["Voice cloning", "Text-to-speech", "Music composition", "Audio stems", "Podcasting"],
        "legacy_categories": ["Voice Generation", "Music Generation"]
    },
    {
        "slug": "code-dev",
        "name": "Code & Dev",
        "icon": "💻",
        "description": "Autonomous coding agents, AI IDEs, code generation, and developer workflow automation.",
        "use_cases": ["Code autocompletion", "Multi-file coding", "Code refactoring", "Bug fixing", "CLI automation"],
        "legacy_categories": ["Code Generation"]
    },
    {
        "slug": "data-analytics",
        "name": "Data & Analytics",
        "icon": "📊",
        "description": "AI data extraction, automated analytics, spreadsheet formulas, and business intelligence.",
        "use_cases": ["Data visualization", "Automated reporting", "SQL generation", "Spreadsheet analysis"],
        "legacy_categories": ["AI Research"]
    },
    {
        "slug": "marketing-seo",
        "name": "Marketing & SEO",
        "icon": "🚀",
        "description": "Automated ad creatives, social media scheduling, SEO optimization, and viral copy generation.",
        "use_cases": ["Ad creatives", "Social media scheduling", "SEO optimization", "Campaign copy"],
        "legacy_categories": ["Marketing & Ads", "Social Media Scheduling"]
    },
    {
        "slug": "productivity-automation",
        "name": "Productivity & Automation",
        "icon": "⚡",
        "description": "Workflow automation engines, AI web builders, presentation makers, and productivity tools.",
        "use_cases": ["Workflow automation", "Website builders", "AI presentations", "Task routing"],
        "legacy_categories": ["Workflow Automation", "Website Builders"]
    },
    {
        "slug": "research-chat",
        "name": "Research & Chat Assistants",
        "icon": "🔍",
        "description": "Frontier reasoning engines, conversational search, academic paper synthesis, and web-grounded research.",
        "use_cases": ["Academic synthesis", "Web-grounded search", "Frontier reasoning", "Document Q&A"],
        "legacy_categories": ["Ideas & Brainstorming", "AI Research"]
    },
    {
        "slug": "business-sales",
        "name": "Business & Sales",
        "icon": "💼",
        "description": "AI sales outreach, CRM automation, customer intelligence, and business deck creators.",
        "use_cases": ["Sales outreach", "CRM enrichment", "Pitch decks", "Client onboarding"],
        "legacy_categories": ["Website Builders", "Marketing & Ads"]
    },
    {
        "slug": "education",
        "name": "Education",
        "icon": "🎓",
        "description": "Personalized AI study tutors, academic consensus finders, research paraphrasers, and learning aids.",
        "use_cases": ["Academic citations", "Study summaries", "Flashcards", "Concept explanation"],
        "legacy_categories": ["AI Research", "AI Writing Assistant"]
    },
    {
        "slug": "agents-workflows",
        "name": "Agents & Workflows",
        "icon": "🤖",
        "description": "Autonomous multi-agent loops, chatbot orchestrators, computer-use agents, and background workers.",
        "use_cases": ["Autonomous agents", "Support chatbots", "API orchestration", "Computer-use loops"],
        "legacy_categories": ["Chatbot & Support", "Workflow Automation"]
    }
]

# Quick lookup by slug
TOP_CATEGORIES_BY_SLUG = {cat["slug"]: cat for cat in TOP_CATEGORIES}

def get_top_category_by_slug(slug: str) -> Dict:
    return TOP_CATEGORIES_BY_SLUG.get(slug)

def get_all_top_categories() -> List[Dict]:
    return TOP_CATEGORIES
