from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReviewCategoryItem(BaseModel):
    category_code: str | None = None
    category_name: str
    score: float | None = None
    score_scale: float | None = None
    display_order: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewCategoryCurrentSummary(BaseModel):
    hotel_id: str
    hotel_name: str
    platform_code: str
    source_captured_at: datetime
    categories: list[ReviewCategoryItem] = Field(default_factory=list)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewCategoryCurrentListResponse(BaseModel):
    items: list[ReviewCategoryCurrentSummary]
    total: int
