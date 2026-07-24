from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.core.config import settings
from app.db.session import SessionLocal
from app.schemas.google_sheets import (
    GoogleSheetsExportAcceptedResponse,
    GoogleSheetsExportRequest,
    GoogleSheetsExportResponse,
)
from app.services.google_sheets_service import GoogleSheetsService

router = APIRouter(tags=["google-sheets"])


@router.post(
    "/exports/google-sheets/reviews",
    response_model=GoogleSheetsExportResponse,
    status_code=status.HTTP_200_OK,
)
def export_reviews_to_google_sheets(
    payload: GoogleSheetsExportRequest,
    db: Session = Depends(db_session),
) -> GoogleSheetsExportResponse:
    service = GoogleSheetsService(db)
    try:
        return service.export_reviews(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def _run_google_sheets_export(payload: GoogleSheetsExportRequest) -> None:
    db = SessionLocal()
    try:
        service = GoogleSheetsService(db)
        service.export_reviews(payload)
    finally:
        db.close()


@router.post(
    "/exports/google-sheets/reviews/async",
    response_model=GoogleSheetsExportAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def export_reviews_to_google_sheets_async(
    payload: GoogleSheetsExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(db_session),
) -> GoogleSheetsExportAcceptedResponse:
    service = GoogleSheetsService(db)
    background_tasks.add_task(_run_google_sheets_export, payload)
    hotels = service.hotel_repository.list_export_hotels(
        hotel_ids=payload.hotel_ids or None,
        only_active_hotels=payload.only_active_hotels,
    )
    hotels = service._filter_enabled_hotels(
        hotels=hotels,
        only_enabled_hotels=payload.only_enabled_hotels,
    )
    return GoogleSheetsExportAcceptedResponse(
        status="queued",
        spreadsheet_id=payload.spreadsheet_id or settings.google_sheets_spreadsheet_id,
        queued_hotels=len(hotels),
    )
