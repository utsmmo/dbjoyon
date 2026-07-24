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
