from pydantic import BaseModel, Field


class InsightReviewItem(BaseModel):
    hotel_name: str
    platform_code: str | None = None
    reviewer_country_code: str | None = None
    rating: float | None = None
    rating_scale: float | None = None
    reviewed_at: str
    is_bad_review: bool
    title: str
    body: str


class InsightCategoryItem(BaseModel):
    label: str
    value: float
    scale: float


class InsightBreakdownItem(BaseModel):
    label: str
    value: int


class ReviewInsightRequest(BaseModel):
    totalMatches: int
    visibleReviewCount: int
    filters: dict[str, str | list[str] | bool | None] = Field(default_factory=dict)
    analyticsSummary: dict[str, object] | None = None
    countryBreakdown: list[InsightBreakdownItem] = Field(default_factory=list)
    hotelBreakdown: list[InsightBreakdownItem] = Field(default_factory=list)
    keywordSummary: list[InsightBreakdownItem] = Field(default_factory=list)
    categories: list[InsightCategoryItem] = Field(default_factory=list)
    reviews: list[InsightReviewItem] = Field(default_factory=list)


class ReviewInsightResponse(BaseModel):
    content: str
