from datetime import datetime

from pydantic import BaseModel, Field


class AdminSettingResponse(BaseModel):
    id: str
    setting_key: str
    group_code: str
    label: str
    description: str | None = None
    value_type: str
    is_secret: bool
    is_editable: bool
    value: str | None = None
    masked_value: str | None = None
    updated_by_user_id: str | None = None
    updated_by_email: str | None = None
    created_at: datetime
    updated_at: datetime


class AdminSettingListResponse(BaseModel):
    items: list[AdminSettingResponse]
    total: int


class AdminSettingUpdateRequest(BaseModel):
    value: str | int | bool | None = Field(default=None)
    updated_by_user_id: str | None = Field(default=None, max_length=64)


class AdminAiProviderValidationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    api_key: str = Field(min_length=1)
    base_url: str = Field(min_length=1)
    model: str = Field(min_length=1, max_length=200)
    timeout_ms: int = Field(ge=1000, le=300000, default=45000)


class AdminAiProviderValidationResponse(BaseModel):
    ok: bool
    message: str
