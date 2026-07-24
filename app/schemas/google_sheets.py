from pydantic import BaseModel, Field


class GoogleSheetsExportRequest(BaseModel):
    spreadsheet_id: str | None = None
    hotel_ids: list[str] = Field(default_factory=list)
    replace_sheet: bool = True
    only_active_hotels: bool = True
    only_enabled_hotels: bool = True


class GoogleSheetsExportHotelResult(BaseModel):
    hotel_id: str
    hotel_name: str
    sheet_title: str
    exported_rows: int


class GoogleSheetsExportResponse(BaseModel):
    spreadsheet_id: str
    exported_hotels: list[GoogleSheetsExportHotelResult]
    total_hotels: int


class GoogleSheetsExportAcceptedResponse(BaseModel):
    status: str
    spreadsheet_id: str
    queued_hotels: int
