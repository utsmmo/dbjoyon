from datetime import datetime
from typing import Literal
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ReviewSummary


class UnnotifiedBadReviewListResponse(BaseModel):
    review_label: Literal["bad", "good", "all"] = "bad"
    channel_code: str
    event_type: str
    items: list[ReviewSummary]
    total: int
    limit: int
    offset: int


class NotificationDeliveryUpsertRequest(BaseModel):
    review_id: str
    channel_code: str = Field(min_length=1, max_length=100)
    event_type: str | None = Field(default=None, min_length=1, max_length=50)
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


class LarkBadReviewSendRequest(BaseModel):
    review_id: str | None = None
    review_ids: list[str] = Field(default_factory=list)
    webhook_url: str | None = None
    target_ref: str | None = None
    review_label: Literal["bad", "good", "all"] = "bad"
    channel_code: str = Field(default="lark", min_length=1, max_length=100)
    event_type: str | None = Field(default=None, min_length=1, max_length=50)
    hotel_id: str | None = None
    platform_code: str | None = None
    recent_days: int = Field(default=10, ge=1, le=60)
    include_sent: bool = False
    limit: int = Field(default=20, ge=1, le=100)


class LarkBadReviewSendItemResponse(BaseModel):
    review_id: str
    hotel_name: str
    platform_code: str
    delivery_status: str
    external_message_id: str | None = None
    error_message: str | None = None
    response_payload: dict[str, Any] = Field(default_factory=dict)
    delivery: NotificationDeliveryUpsertResponse | None = None


class LarkBadReviewSendResponse(BaseModel):
    channel_code: str
    event_type: str
    target_ref: str | None = None
    requested_count: int
    processed_count: int
    sent_count: int
    failed_count: int
    items: list[LarkBadReviewSendItemResponse] = Field(default_factory=list)
