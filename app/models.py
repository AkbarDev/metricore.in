from typing import Optional, List
from pydantic import BaseModel

class AITool(BaseModel):
    id: str
    name: str
    category: str
    pricing_type: str  # "Paid" or "Free"
    price_display: str
    free_tier_details: str
    free_tier_limit: str
    description: str
    url: str
    image_url: Optional[str] = None
    image_alt: Optional[str] = None
    alternative_id: Optional[str] = None

    # Pricing audit
    price_last_checked: Optional[str] = None
    price_source_url: Optional[str] = None

    # Provenance & Company
    facts_source_url: Optional[str] = None
    founded_year: Optional[int] = None
    founders: Optional[str] = None
    country_name: Optional[str] = None
    country_flag: Optional[str] = None
    github_stars: Optional[str] = None
    operational_status: Optional[str] = "Active"
    total_funding: Optional[str] = None
    relevancy_2026: Optional[str] = None

    # Builder Evaluation Metrics (2026/2027 Stack)
    eval_api_readiness: Optional[str] = None
    eval_license_risk: Optional[str] = None
    eval_compliance: Optional[str] = None
    eval_scalability: Optional[str] = None
    eval_recency: Optional[str] = None
    eval_ecosystem: Optional[str] = None

    # Efficiency, Accuracy & Modality Metrics
    modality_type: Optional[str] = None
    eval_latency: Optional[str] = None
    eval_accuracy_tier: Optional[str] = None

    # Category Page Architecture & Modern Taxonomy
    top_category_slug: Optional[str] = None
    top_category_name: Optional[str] = None
    tagline: Optional[str] = None
    tags: List[str] = []
    platforms: List[str] = []
    pricing_tier: Optional[str] = None
    use_cases: List[str] = []
    is_top_pick: bool = False
    rating: Optional[float] = None
    reviews_count: Optional[int] = None

class PublicAITool(BaseModel):
    """Public representation strictly omitting rating, reviews_count, eval_compliance, eval_license_risk, founders, and total_funding."""
    id: str
    name: str
    category: str
    pricing_type: str
    price_display: str
    free_tier_details: str
    free_tier_limit: str
    description: str
    url: str
    image_url: Optional[str] = None
    image_alt: Optional[str] = None
    alternative_id: Optional[str] = None

    price_last_checked: Optional[str] = None
    price_source_url: Optional[str] = None
    facts_source_url: Optional[str] = None

    founded_year: Optional[int] = None
    country_name: Optional[str] = None
    country_flag: Optional[str] = None
    github_stars: Optional[str] = None
    operational_status: Optional[str] = "Active"
    relevancy_2026: Optional[str] = None

    eval_api_readiness: Optional[str] = None
    eval_scalability: Optional[str] = None
    eval_recency: Optional[str] = None
    eval_ecosystem: Optional[str] = None

    modality_type: Optional[str] = None
    eval_latency: Optional[str] = None
    eval_accuracy_tier: Optional[str] = None

    top_category_slug: Optional[str] = None
    top_category_name: Optional[str] = None
    tagline: Optional[str] = None
    tags: List[str] = []
    platforms: List[str] = []
    pricing_tier: Optional[str] = None
    use_cases: List[str] = []
    is_top_pick: bool = False

class TopCategoryInfo(BaseModel):
    slug: str
    name: str
    description: str
    icon: str
    use_cases: List[str] = []
    count: int = 0

class CategorySummary(BaseModel):
    name: str
    count: int
    paid_tool: Optional[AITool] = None
    free_tool: Optional[AITool] = None
