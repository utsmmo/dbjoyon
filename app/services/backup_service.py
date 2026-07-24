from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.schemas.backup import BackupConfigResponse, BackupRunResponse


class BackupService:
    def __init__(self) -> None:
        self.local_dir = Path(settings.backup_local_dir)
        self.local_dir.mkdir(parents=True, exist_ok=True)

    def get_config(self) -> BackupConfigResponse:
        return BackupConfigResponse(
            backup_enabled=settings.backup_enabled,
            backup_local_dir=str(self.local_dir),
            backup_drive_remote=settings.backup_drive_remote or None,
            backup_drive_root_folder=settings.backup_drive_root_folder,
            backup_drive_daily_subfolders=settings.backup_drive_daily_subfolders,
            backup_keep_local_days=settings.backup_keep_local_days,
            backup_db_host=settings.backup_db_host or "postgres",
            backup_db_port=settings.backup_db_port or 5432,
            backup_db_name=settings.backup_db_name or "",
            backup_db_user=settings.backup_db_user or "",
        )

    def run_backup(
        self,
        *,
        folder_date: str | None,
        subfolder: str | None,
        keep_local_days: int | None,
    ) -> BackupRunResponse:
        if not settings.backup_enabled:
            raise RuntimeError("Backup feature is disabled.")

        started_at = datetime.now()
        effective_keep_days = keep_local_days if keep_local_days is not None else settings.backup_keep_local_days
        date_folder = folder_date or started_at.strftime("%Y-%m-%d")
        timestamp = started_at.strftime("%Y%m%d-%H%M%S")
        backup_file_name = f"{settings.backup_db_name}-{timestamp}.dump"
        local_backup_path = self.local_dir / backup_file_name

        env = os.environ.copy()
        env["PGPASSWORD"] = settings.backup_db_password or ""
        if settings.backup_rclone_config_path:
            env["RCLONE_CONFIG"] = settings.backup_rclone_config_path

        dump_command = [
            "pg_dump",
            "-h",
            settings.backup_db_host or "postgres",
            "-p",
            str(settings.backup_db_port or 5432),
            "-U",
            settings.backup_db_user or "",
            "-d",
            settings.backup_db_name or "",
            "-Fc",
            "-f",
            str(local_backup_path),
        ]
        subprocess.run(dump_command, check=True, env=env)

        remote_target = None
        remote_file_path = None
        if settings.backup_drive_remote:
            remote_parts = [settings.backup_drive_root_folder.strip("/")]
            if subfolder:
                remote_parts.append(subfolder.strip("/"))
            if settings.backup_drive_daily_subfolders:
                remote_parts.append(date_folder)
            remote_path = "/".join(part for part in remote_parts if part)
            remote_target = f"{settings.backup_drive_remote}:{remote_path}"
            remote_file_path = f"{remote_target}/{backup_file_name}"
            subprocess.run(["rclone", "copy", str(local_backup_path), remote_target], check=True, env=env)

        if effective_keep_days > 0:
            cutoff = datetime.now().timestamp() - (effective_keep_days * 86400)
            for file_path in self.local_dir.glob("*.dump"):
                if file_path.stat().st_mtime < cutoff:
                    file_path.unlink(missing_ok=True)

        finished_at = datetime.now()
        return BackupRunResponse(
            status="success",
            backup_file_name=backup_file_name,
            local_backup_path=str(local_backup_path),
            remote_target=remote_target,
            remote_file_path=remote_file_path,
            file_size_bytes=local_backup_path.stat().st_size,
            started_at=started_at,
            finished_at=finished_at,
        )
