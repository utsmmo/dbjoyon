from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TimestampedModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ReviewSummary(TimestampedModel):
    id: str
    hotel_id: str
    hotel_name: str
    platform_code: str
    external_review_id: str
    reviewer_name: str | None
    reviewer_country_code: str | None
    rating: float | None
    rating_scale: float | None
    review_title: str | None
    review_text: str | None
    translated_title_vi: str | None = None
    translated_text_vi: str | None = None
    review_language: str | None
    sentiment_label: str | None
    is_bad_review: bool
    stay_date: date | None
    reviewed_at: datetime
    replied_at: datetime | None
    source_updated_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ReviewStatsSummary(TimestampedModel):
    hotel_id: str
    platform_code: str
    total_reviews: int
    bad_reviews: int
    latest_reviewed_at: datetime | None
    latest_source_updated_at: datetime | None


class IncidentSummary(TimestampedModel):
    id: str
    hotel_id: str
    review_id: str | None
    incident_type: str
    severity: str
    status: str
    title: str
    description: str | None
    detected_at: datetime
    resolved_at: datetime | None
    owner_name: str | None
    metadata: dict[str, Any]
