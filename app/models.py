from typing import Optional, List
from pydantic import BaseModel, HttpUrl

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
    alternative_id: Optional[str] = None

    # Provenance & Company
    founded_year: Optional[int] = None
    founders: Optional[str] = None
    country_name: Optional[str] = None
    country_flag: Optional[str] = None
    github_stars: Optional[str] = None
    operational_status: Optional[str] = "Active"
    total_funding: Optional[str] = None
    relevancy_2026: Optional[str] = None

    # 6 Builder Evaluation Metrics (2026/2027 Stack)
    eval_api_readiness: Optional[str] = None
    eval_license_risk: Optional[str] = None
    eval_compliance: Optional[str] = None
    eval_scalability: Optional[str] = None
    eval_recency: Optional[str] = None
    eval_ecosystem: Optional[str] = None

    # Efficiency, Accuracy & Modality Metrics
    modality_type: Optional[str] = None          # "Image / Visual", "Sound / Audio / Music", "Video / Motion", "Text / Writing", "Code / Dev", "Workflow / Automation", "Research & Reasoning"
    eval_latency: Optional[str] = None           # "Real-time (<500ms)", "Interactive (1s-3s)", "Batch (5s+)"
    eval_accuracy_tier: Optional[str] = None     # "Frontier Reasoning", "Web Grounded with Citations", "High-Fidelity Generative"

class CategorySummary(BaseModel):
    name: str
    count: int
    paid_tool: Optional[AITool] = None
    free_tool: Optional[AITool] = None

