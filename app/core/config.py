from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import make_url


class Settings(BaseSettings):
    app_env: str = "local"
    app_version: str = "0.1.10"
    app_build: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "postgresql+psycopg://hotel_admin:hotel_admin_123@localhost:15432/hotel_review_db"
    default_timezone: str = "Asia/Bangkok"
    bad_review_rating_threshold: float = 9.0
    translation_provider: str = "disabled"
    google_translate_enabled: bool = False
    google_translate_api_key: str = ""
    google_translate_target_language: str = "vi"
    google_translate_timeout_seconds: int = 15
    backup_enabled: bool = True
    backup_local_dir: str = "/app/backups"
    backup_drive_remote: str = ""
    backup_drive_root_folder: str = "hotel-review-backup"
    backup_drive_daily_subfolders: bool = True
    backup_keep_local_days: int = 14
    backup_db_host: str | None = None
    backup_db_port: int | None = None
    backup_db_name: str | None = None
    backup_db_user: str | None = None
    backup_db_password: str | None = None
    backup_rclone_config_path: str | None = None
    google_sheets_spreadsheet_id: str = ""
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_refresh_token: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()


db_url = make_url(settings.database_url)
settings.backup_db_host = settings.backup_db_host or (db_url.host or "postgres")
settings.backup_db_port = settings.backup_db_port or int(db_url.port or 5432)
settings.backup_db_name = settings.backup_db_name or (db_url.database or "hotel_review_db")
settings.backup_db_user = settings.backup_db_user or (db_url.username or "hotel_admin")
settings.backup_db_password = settings.backup_db_password or (db_url.password or "")
settings.backup_local_dir = str(Path(settings.backup_local_dir))
