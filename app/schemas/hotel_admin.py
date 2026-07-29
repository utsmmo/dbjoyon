from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from app.schemas.hotel import HotelCreateRequest


class HotelImportItem(BaseModel):
    hotel_code: str = Field(min_length=1, max_length=50)
    hotel_name: str = Field(min_length=1, max_length=255)
    timezone: str = "Asia/Bangkok"
    country_code: str | None = None
    city: str | None = None
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)
    links: dict[str, list[str]] = Field(default_factory=dict)


class HotelPurgeRequest(BaseModel):
    confirm_purge: bool = False


class HotelResetImportRequest(BaseModel):
    confirm_purge: bool = False
    hotels: list[HotelImportItem] = Field(default_factory=list)


class HotelAdminUpsertRequest(HotelCreateRequest):
    links: dict[str, list[str]] = Field(default_factory=dict)


class HotelImportSummary(BaseModel):
    hotel_id: str
    hotel_code: str
    hotel_name: str
    accounts_created: int
    normalized_links: dict[str, list[str]]


class HotelPurgeResponse(BaseModel):
    deleted_hotels: int
    deleted_at: datetime
    status: str


class HotelResetImportResponse(BaseModel):
    deleted_hotels: int
    imported_hotels: int
    imported_accounts: int
    items: list[HotelImportSummary]
    imported_at: datetime
    status: str


class HotelDeleteResponse(BaseModel):
    deleted_hotel_id: str
    deleted_at: datetime
    status: str
