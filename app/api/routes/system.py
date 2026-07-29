from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.backup import BackupConfigResponse, BackupRunRequest, BackupRunResponse
from app.schemas.hotel_admin import (
    HotelAdminUpsertRequest,
    HotelDeleteResponse,
    HotelPurgeRequest,
    HotelPurgeResponse,
    HotelResetImportRequest,
    HotelResetImportResponse,
)
from app.schemas.hotel import HotelResponse
from app.services.backup_service import BackupService
from app.services.hotel_service import HotelService

router = APIRouter(tags=["system"])


@router.get("/system/backup/config", response_model=BackupConfigResponse)
def get_backup_config() -> BackupConfigResponse:
    service = BackupService()
    return service.get_config()


@router.post("/system/backup/run", response_model=BackupRunResponse)
def run_backup(payload: BackupRunRequest | None = None) -> BackupRunResponse:
    service = BackupService()
    request = payload or BackupRunRequest()
    return service.run_backup(
        folder_date=request.folder_date,
        subfolder=request.subfolder,
        keep_local_days=request.keep_local_days,
    )


@router.post("/system/hotels/purge", response_model=HotelPurgeResponse)
def purge_hotels(
    payload: HotelPurgeRequest,
    db: Session = Depends(db_session),
) -> HotelPurgeResponse:
    service = HotelService(db)
    try:
        return service.purge_all_hotels(confirm_purge=payload.confirm_purge)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/system/hotels/reset-import", response_model=HotelResetImportResponse)
def reset_and_import_hotels(
    payload: HotelResetImportRequest,
    db: Session = Depends(db_session),
) -> HotelResetImportResponse:
    service = HotelService(db)
    try:
        return service.reset_and_import_hotels(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/system/hotels/reset-import/default-manifest", response_model=HotelResetImportResponse)
def reset_and_import_default_manifest(
    payload: HotelPurgeRequest,
    db: Session = Depends(db_session),
) -> HotelResetImportResponse:
    service = HotelService(db)
    try:
        return service.reset_and_import_default_manifest(
            confirm_purge=payload.confirm_purge
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/system/hotels", response_model=HotelResponse)
def create_admin_hotel(
    payload: HotelAdminUpsertRequest,
    db: Session = Depends(db_session),
) -> HotelResponse:
    service = HotelService(db)
    try:
        return service.create_admin_hotel(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/system/hotels/{hotel_id}", response_model=HotelResponse)
def update_admin_hotel(
    hotel_id: str,
    payload: HotelAdminUpsertRequest,
    db: Session = Depends(db_session),
) -> HotelResponse:
    service = HotelService(db)
    try:
        return service.update_admin_hotel(hotel_id=hotel_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/system/hotels/{hotel_id}", response_model=HotelDeleteResponse)
def delete_admin_hotel(
    hotel_id: str,
    db: Session = Depends(db_session),
) -> HotelDeleteResponse:
    service = HotelService(db)
    try:
        return service.delete_admin_hotel(hotel_id=hotel_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
