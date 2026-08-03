from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.admin_settings import (
    AdminSettingListResponse,
    AdminSettingResponse,
    AdminSettingUpdateRequest,
)
from app.services.admin_settings_service import AdminSettingsService

router = APIRouter(prefix="/admin/settings", tags=["admin-settings"])


@router.get("", response_model=AdminSettingListResponse)
def list_settings(db: Session = Depends(db_session)) -> AdminSettingListResponse:
    service = AdminSettingsService(db)
    try:
        return service.list_settings()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{setting_key:path}", response_model=AdminSettingResponse)
def update_setting(
    setting_key: str,
    payload: AdminSettingUpdateRequest,
    db: Session = Depends(db_session),
) -> AdminSettingResponse:
    service = AdminSettingsService(db)
    try:
        return service.update_setting(setting_key=setting_key, payload=payload)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
