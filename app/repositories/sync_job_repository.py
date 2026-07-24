from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories._json import to_jsonb_param


class SyncJobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(
        self,
        *,
        job_type: str,
        target_type: str,
        hotel_id: str,
        platform_id: str,
        hotel_platform_account_id: str | None,
        triggered_by: str,
        request_payload: dict[str, Any],
    ) -> str:
        result = self.db.execute(
            text(
                """
                INSERT INTO sync_jobs (
                    job_type,
                    target_type,
                    hotel_id,
                    platform_id,
                    hotel_platform_account_id,
                    triggered_by,
                    status,
                    request_payload,
                    started_at
                )
                VALUES (
                    :job_type,
                    :target_type,
                    CAST(:hotel_id AS uuid),
                    CAST(:platform_id AS uuid),
                    CAST(:hotel_platform_account_id AS uuid),
                    :triggered_by,
                    'running',
                    CAST(:request_payload AS jsonb),
                    NOW()
                )
                RETURNING id::text
                """
            ),
            {
                "job_type": job_type,
                "target_type": target_type,
                "hotel_id": hotel_id,
                "platform_id": platform_id,
                "hotel_platform_account_id": hotel_platform_account_id,
                "triggered_by": triggered_by,
                "request_payload": to_jsonb_param(request_payload),
            },
        )
        return str(result.scalar_one())

    def finish_job(
        self,
        *,
        sync_job_id: str,
        status: str,
        records_fetched: int,
        records_inserted: int,
        records_updated: int,
        response_payload: dict[str, Any],
        error_message: str | None = None,
    ) -> None:
        self.db.execute(
            text(
                """
                UPDATE sync_jobs
                SET status = :status,
                    records_fetched = :records_fetched,
                    records_inserted = :records_inserted,
                    records_updated = :records_updated,
                    response_payload = CAST(:response_payload AS jsonb),
                    error_message = :error_message,
                    finished_at = NOW(),
                    updated_at = NOW()
                WHERE id = CAST(:sync_job_id AS uuid)
                """
            ),
            {
                "sync_job_id": sync_job_id,
                "status": status,
                "records_fetched": records_fetched,
                "records_inserted": records_inserted,
                "records_updated": records_updated,
                "response_payload": to_jsonb_param(response_payload),
                "error_message": error_message,
            },
        )
