from fastapi import APIRouter

from app.schemas.backup import BackupConfigResponse, BackupRunRequest, BackupRunResponse
from app.services.backup_service import BackupService

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
