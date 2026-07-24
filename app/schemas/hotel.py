from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HotelCreateRequest(BaseModel):
    hotel_code: str = Field(min_length=1, max_length=50)
    hotel_name: str = Field(min_length=1, max_length=255)
    legal_name: str | None = None
    timezone: str = "Asia/Bangkok"
    country_code: str | None = None
    city: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    postal_code: str | None = None
    phone: str | None = None
    email: str | None = None
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)


class HotelResponse(BaseModel):
    id: str
    hotel_code: str
    hotel_name: str
    legal_name: str | None
    timezone: str
    country_code: str | None
    city: str | None
    address_line1: str | None
    address_line2: str | None
    postal_code: str | None
    phone: str | None
    email: str | None
    status: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class HotelListResponse(BaseModel):
    items: list[HotelResponse]
    total: int
    limit: int
    offset: int
