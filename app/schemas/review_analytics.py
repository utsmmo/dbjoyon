from datetime import date, datetime

from pydantic import BaseModel


class ReviewSummaryAggregateResponse(BaseModel):
    hotel_id: str | None = None
    platform_code: str | None = None
    reviewer_country_code: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    total_reviews: int = 0
    bad_reviews: int = 0
    bad_review_ratio: float = 0.0
    avg_rating: float | None = None
    positive_reviews: int | None = None
    neutral_reviews: int | None = None
    negative_reviews: int | None = None
    mixed_reviews: int | None = None
    latest_reviewed_at: datetime | None = None
    latest_source_updated_at: datetime | None = None
    source_total_reviews: int | None = None
    source_average_rating: float | None = None
    source_rating_scale: float | None = None
    last_aggregated_at: datetime | None = None


class ReviewCountryBreakdownItem(BaseModel):
    reviewer_country_code: str
    total_reviews: int
    bad_reviews: int
    avg_rating: float | None = None


class ReviewCountryBreakdownResponse(BaseModel):
    items: list[ReviewCountryBreakdownItem]
    total: int


class ReviewHotelBreakdownItem(BaseModel):
    hotel_id: str
    hotel_name: str
    platform_code: str | None = None
    total_reviews: int
    bad_reviews: int
    avg_rating: float | None = None
    latest_reviewed_at: datetime | None = None


class ReviewHotelBreakdownResponse(BaseModel):
    items: list[ReviewHotelBreakdownItem]
    total: int


class ReviewScoreBucketItem(BaseModel):
    bucket_code: str
    bucket_label: str
    rating_from: float
    rating_to: float
    review_count: int
    bad_review_count: int


class ReviewScoreBucketsResponse(BaseModel):
    items: list[ReviewScoreBucketItem]
    total: int


class ReviewDailyTrendItem(BaseModel):
    metric_date: date
    total_reviews: int
    bad_reviews: int
    avg_rating: float | None = None
    positive_reviews: int | None = None
    neutral_reviews: int | None = None
    negative_reviews: int | None = None
    mixed_reviews: int | None = None


class ReviewDailyTrendResponse(BaseModel):
    items: list[ReviewDailyTrendItem]
    total: int
