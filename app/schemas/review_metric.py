from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReviewMetricSummary(BaseModel):
    hotel_id: str
    hotel_name: str
    platform_code: str
    source_total_reviews: int | None = None
    source_average_rating: float | None = None
    source_rating_scale: float | None = None
    source_review_url: str | None = None
    source_captured_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewMetricListResponse(BaseModel):
    items: list[ReviewMetricSummary]
    total: int
