from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories._json import to_jsonb_param


class ReviewCategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_category_snapshot(
        self,
        *,
        hotel_id: str,
        platform_id: str,
        hotel_platform_account_id: str | None,
        source_captured_at: str | None,
        categories_payload: list[dict[str, Any]],
        raw_payload: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO hotel_platform_category_snapshots (
                    hotel_id,
                    platform_id,
                    hotel_platform_account_id,
                    source_captured_at,
                    categories_payload,
                    raw_payload,
                    metadata
                )
                VALUES (
                    CAST(:hotel_id AS uuid),
                    CAST(:platform_id AS uuid),
                    CAST(:hotel_platform_account_id AS uuid),
                    COALESCE(CAST(:source_captured_at AS timestamptz), NOW()),
                    CAST(:categories_payload AS jsonb),
                    CAST(:raw_payload AS jsonb),
                    CAST(:metadata AS jsonb)
                )
                ON CONFLICT (hotel_id, platform_id, source_captured_at)
                DO UPDATE SET
                    hotel_platform_account_id = EXCLUDED.hotel_platform_account_id,
                    categories_payload = EXCLUDED.categories_payload,
                    raw_payload = EXCLUDED.raw_payload,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                """
            ),
            {
                "hotel_id": hotel_id,
                "platform_id": platform_id,
                "hotel_platform_account_id": hotel_platform_account_id,
                "source_captured_at": source_captured_at,
                "categories_payload": to_jsonb_param(categories_payload),
                "raw_payload": to_jsonb_param(raw_payload),
                "metadata": to_jsonb_param(metadata),
            },
        )

    def list_current_categories(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
    ) -> list[dict[str, Any]]:
        filters = ["1 = 1"]
        params: dict[str, Any] = {}

        if hotel_id:
            filters.append("c.hotel_id = CAST(:hotel_id AS uuid)")
            params["hotel_id"] = hotel_id
        if platform_code:
            filters.append("p.platform_code = :platform_code")
            params["platform_code"] = platform_code

        where_clause = " AND ".join(filters)
        result = self.db.execute(
            text(
                f"""
                WITH ranked AS (
                    SELECT
                        c.hotel_id,
                        c.platform_id,
                        c.source_captured_at,
                        c.categories_payload,
                        c.raw_payload,
                        c.metadata,
                        ROW_NUMBER() OVER (
                            PARTITION BY c.hotel_id, c.platform_id
                            ORDER BY c.source_captured_at DESC, c.created_at DESC
                        ) AS rn
                    FROM hotel_platform_category_snapshots c
                    JOIN platforms p ON p.id = c.platform_id
                    WHERE {where_clause}
                )
                SELECT
                    r.hotel_id::text AS hotel_id,
                    h.hotel_name,
                    p.platform_code,
                    r.source_captured_at,
                    r.categories_payload,
                    r.raw_payload,
                    r.metadata
                FROM ranked r
                JOIN hotels h ON h.id = r.hotel_id
                JOIN platforms p ON p.id = r.platform_id
                WHERE r.rn = 1
                ORDER BY h.hotel_name, p.platform_code
                """
            ),
            params,
        )
        return [dict(row) for row in result.mappings().all()]
