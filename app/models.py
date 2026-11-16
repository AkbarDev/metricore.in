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
    alternative_id: Optional[str] = None

class CategorySummary(BaseModel):
    name: str
    count: int
    paid_tool: Optional[AITool] = None
    free_tool: Optional[AITool] = None

