from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ReviewSummary


class UnnotifiedBadReviewListResponse(BaseModel):
    channel_code: str
    event_type: str
    items: list[ReviewSummary]
    total: int
    limit: int
    offset: int


class NotificationDeliveryUpsertRequest(BaseModel):
    review_id: str
    channel_code: str = Field(min_length=1, max_length=100)
    event_type: str = Field(default="bad_review", min_length=1, max_length=50)
    delivery_status: str = Field(min_length=1, max_length=30)
    target_ref: str | None = None
    external_message_id: str | None = None
    error_message: str | None = None
    request_payload: dict[str, Any] = Field(default_factory=dict)
    response_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationDeliveryUpsertResponse(BaseModel):
    id: str
    review_id: str
    channel_code: str
    event_type: str
    delivery_status: str
    attempt_count: int
    external_message_id: str | None
    sent_at: datetime | None
    updated_at: datetime
