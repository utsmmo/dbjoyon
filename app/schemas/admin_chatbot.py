from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


BotStatus = Literal["draft", "pilot", "active", "paused"]
KnowledgeStatus = Literal["draft", "review", "published", "archived"]
RuntimeSourceGroup = Literal["price", "inventory", "booking_status"]
RuntimeSourceType = Literal["table", "view", "api"]


class ChatbotHotelSettingsResponse(BaseModel):
    hotel_id: str
    hotel_name: str
    hotel_code: str
    bot_status: BotStatus
    default_language: str
    supported_languages: list[str]
    confidence_threshold: float
    handoff_threshold: float
    allow_auto_reply: bool
    allow_after_hours_reply: bool
    allow_price_quote: bool
    allow_inventory_lookup: bool
    allow_booking_status_lookup: bool
    handoff_channel_code: str | None = None
    handoff_target_ref: str | None = None
    business_hours_json: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None
    updated_by_user_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ChatbotHotelSettingsListResponse(BaseModel):
    items: list[ChatbotHotelSettingsResponse]
    total: int


class ChatbotHotelSettingsUpdateRequest(BaseModel):
    bot_status: BotStatus
    default_language: str = Field(min_length=2, max_length=20)
    supported_languages: list[str] = Field(default_factory=list)
    confidence_threshold: float = Field(ge=0, le=1)
    handoff_threshold: float = Field(ge=0, le=1)
    allow_auto_reply: bool = False
    allow_after_hours_reply: bool = True
    allow_price_quote: bool = False
    allow_inventory_lookup: bool = False
    allow_booking_status_lookup: bool = False
    handoff_channel_code: str | None = Field(default=None, max_length=100)
    handoff_target_ref: str | None = Field(default=None, max_length=255)
    business_hours_json: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None
    updated_by_user_id: str | None = Field(default=None, max_length=64)


class ChatbotKnowledgeSourceResponse(BaseModel):
    id: str
    hotel_id: str
    hotel_name: str
    hotel_code: str
    document_type: str
    title: str
    content: str
    language: str
    status: KnowledgeStatus
    source_ref: str
    version: int
    tags_json: list[str] = Field(default_factory=list)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    published_at: datetime | None = None
    published_by_user_id: str | None = None
    synced_document_id: str | None = None
    last_sync_job_id: str | None = None
    last_sync_status: str | None = None
    last_synced_at: datetime | None = None
    chunk_count: int = 0
    updated_by_user_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ChatbotKnowledgeSourceListResponse(BaseModel):
    items: list[ChatbotKnowledgeSourceResponse]
    total: int
    limit: int
    offset: int


class ChatbotKnowledgeSourceUpsertRequest(BaseModel):
    hotel_id: str
    document_type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    language: str = Field(min_length=2, max_length=20)
    status: KnowledgeStatus = "draft"
    source_ref: str = Field(min_length=1, max_length=255)
    version: int = Field(ge=1)
    tags_json: list[str] = Field(default_factory=list)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    updated_by_user_id: str | None = Field(default=None, max_length=64)


class ChatbotKnowledgePublishRequest(BaseModel):
    published_by_user_id: str | None = Field(default=None, max_length=64)


class ChatbotKnowledgeSyncRequest(BaseModel):
    triggered_by_user_id: str | None = Field(default=None, max_length=64)


class ChatbotKnowledgeSyncResponse(BaseModel):
    job_id: str
    source_id: str
    document_id: str
    chunk_count: int
    status: str
    synced_at: datetime


class ChatbotRuntimeSourceResponse(BaseModel):
    id: str
    hotel_id: str
    hotel_name: str
    hotel_code: str
    source_group: RuntimeSourceGroup
    source_code: str
    source_type: RuntimeSourceType
    connection_name: str
    target_ref: str
    query_template: str | None = None
    mapping_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    last_checked_at: datetime | None = None
    last_status: str
    last_error_message: str | None = None
    updated_by_user_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ChatbotRuntimeSourceListResponse(BaseModel):
    items: list[ChatbotRuntimeSourceResponse]
    total: int


class ChatbotRuntimeSourceUpsertRequest(BaseModel):
    hotel_id: str
    source_group: RuntimeSourceGroup
    source_code: str = Field(min_length=1, max_length=100)
    source_type: RuntimeSourceType
    connection_name: str = Field(min_length=1, max_length=100)
    target_ref: str = Field(min_length=1, max_length=255)
    query_template: str | None = None
    mapping_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    updated_by_user_id: str | None = Field(default=None, max_length=64)


class ChatbotRuntimeSourceTestResponse(BaseModel):
    id: str
    status: str
    checked_at: datetime
    sample_result: dict[str, Any] | None = None
    error_message: str | None = None
