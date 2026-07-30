from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ExternalReviewPayload(BaseModel):
    external_review_id: str = Field(min_length=1, max_length=255)
    reviewed_at: datetime
    source_created_at: datetime | None = None
    source_updated_at: datetime | None = None
    review_url: str | None = None
    reviewer_name: str | None = None
    reviewer_country_code: str = Field(min_length=2, max_length=2)
    rating: float | None = None
    rating_scale: float | None = None
    review_title: str | None = None
    review_text: str | None = None
    review_language: str | None = None
    stay_date: date | None = None
    replied_at: datetime | None = None
    sentiment_label: str | None = None
    is_bad_review: bool | None = None
    reviewer_profile: dict[str, Any] = Field(default_factory=dict)
    normalized_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reviewer_country_code")
    @classmethod
    def normalize_reviewer_country_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 2 or not normalized.isalpha():
            raise ValueError("reviewer_country_code must be a 2-letter ISO country code")
        return normalized


class SourceCategoryPayload(BaseModel):
    category_code: str | None = None
    category_name: str
    score: float | None = None
    score_scale: float | None = None
    display_order: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SyncReviewsRequest(BaseModel):
    hotel_id: UUID
    hotel_platform_account_id: UUID | None = None
    source_link_used: str | None = None
    triggered_by: str = "api"
    source_total_reviews: int | None = None
    source_average_rating: float | None = None
    source_rating_scale: float | None = None
    source_review_url: str | None = None
    source_captured_at: datetime | None = None
    source_metrics_payload: dict[str, Any] = Field(default_factory=dict)
    source_categories: list[SourceCategoryPayload] = Field(default_factory=list)
    source_category_payload: dict[str, Any] = Field(default_factory=dict)
    reviews: list[ExternalReviewPayload] = Field(default_factory=list)


class SyncReviewsResponse(BaseModel):
    sync_job_id: str
    hotel_id: UUID
    platform_code: str
    source_total_reviews: int | None = None
    source_average_rating: float | None = None
    source_rating_scale: float | None = None
    source_review_url: str | None = None
    source_captured_at: datetime | None = None
    estimated_new_reviews_from_source: int | None = None
    stored_total_reviews_before_sync: int
    stored_total_reviews_after_sync: int
    fetched: int
    inserted: int
    updated: int
    incidents_opened: int
    status: str
