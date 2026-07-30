from pydantic import BaseModel

from app.schemas.common import ReviewStatsSummary, ReviewSummary


class ReviewListResponse(BaseModel):
    items: list[ReviewSummary]
    total: int
    limit: int
    offset: int


class ReviewStatsListResponse(BaseModel):
    items: list[ReviewStatsSummary]
    total: int


class ReviewDeleteResponse(BaseModel):
    review_id: str | None = None
    hotel_id: str
    platform_code: str
    source_link: str | None = None
    deleted_reviews: int
    deleted_review_metrics: int
    deleted_category_snapshots: int
    status: str
