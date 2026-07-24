from datetime import datetime

from pydantic import BaseModel, Field


class BackupRunRequest(BaseModel):
    folder_date: str | None = Field(default=None, description="Override folder date in YYYY-MM-DD format")
    subfolder: str | None = Field(default=None, description="Optional subfolder inside remote root folder")
    keep_local_days: int | None = Field(default=None, ge=0, le=3650)


class BackupRunResponse(BaseModel):
    status: str
    backup_file_name: str
    local_backup_path: str
    remote_target: str | None
    remote_file_path: str | None
    file_size_bytes: int
    started_at: datetime
    finished_at: datetime


class BackupConfigResponse(BaseModel):
    backup_enabled: bool
    backup_local_dir: str
    backup_drive_remote: str | None
    backup_drive_root_folder: str
    backup_drive_daily_subfolders: bool
    backup_keep_local_days: int
    backup_db_host: str
    backup_db_port: int
    backup_db_name: str
    backup_db_user: str
