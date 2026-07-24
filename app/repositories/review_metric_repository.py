from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories._json import to_jsonb_param


class ReviewMetricRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_current_metrics(
        self,
        *,
        hotel_id: str,
        platform_id: str,
        hotel_platform_account_id: str | None,
        source_total_reviews: int | None,
        source_average_rating: float | None,
        source_rating_scale: float | None,
        source_review_url: str | None,
        source_captured_at: str | None,
        raw_payload: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO hotel_platform_review_metrics (
                    hotel_id,
                    platform_id,
                    hotel_platform_account_id,
                    source_total_reviews,
                    source_average_rating,
                    source_rating_scale,
                    source_review_url,
                    source_captured_at,
                    raw_payload,
                    metadata
                )
                VALUES (
                    CAST(:hotel_id AS uuid),
                    CAST(:platform_id AS uuid),
                    CAST(:hotel_platform_account_id AS uuid),
                    :source_total_reviews,
                    :source_average_rating,
                    :source_rating_scale,
                    :source_review_url,
                    COALESCE(CAST(:source_captured_at AS timestamptz), NOW()),
                    CAST(:raw_payload AS jsonb),
                    CAST(:metadata AS jsonb)
                )
                ON CONFLICT (hotel_id, platform_id)
                DO UPDATE SET
                    hotel_platform_account_id = EXCLUDED.hotel_platform_account_id,
                    source_total_reviews = EXCLUDED.source_total_reviews,
                    source_average_rating = EXCLUDED.source_average_rating,
                    source_rating_scale = EXCLUDED.source_rating_scale,
                    source_review_url = EXCLUDED.source_review_url,
                    source_captured_at = EXCLUDED.source_captured_at,
                    raw_payload = EXCLUDED.raw_payload,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                """
            ),
            {
                "hotel_id": hotel_id,
                "platform_id": platform_id,
                "hotel_platform_account_id": hotel_platform_account_id,
                "source_total_reviews": source_total_reviews,
                "source_average_rating": source_average_rating,
                "source_rating_scale": source_rating_scale,
                "source_review_url": source_review_url,
                "source_captured_at": source_captured_at,
                "raw_payload": to_jsonb_param(raw_payload),
                "metadata": to_jsonb_param(metadata),
            },
        )

    def list_current_metrics(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
    ) -> list[dict[str, Any]]:
        filters = ["1 = 1"]
        params: dict[str, Any] = {}

        if hotel_id:
            filters.append("m.hotel_id = CAST(:hotel_id AS uuid)")
            params["hotel_id"] = hotel_id

        if platform_code:
            filters.append("p.platform_code = :platform_code")
            params["platform_code"] = platform_code

        where_clause = " AND ".join(filters)
        result = self.db.execute(
            text(
                f"""
                SELECT
                    m.hotel_id::text AS hotel_id,
                    h.hotel_name,
                    p.platform_code,
                    m.source_total_reviews,
                    m.source_average_rating::float8 AS source_average_rating,
                    m.source_rating_scale::float8 AS source_rating_scale,
                    m.source_review_url,
                    m.source_captured_at,
                    m.metadata
                FROM hotel_platform_review_metrics m
                JOIN hotels h ON h.id = m.hotel_id
                JOIN platforms p ON p.id = m.platform_id
                WHERE {where_clause}
                ORDER BY h.hotel_name, p.platform_code
                """
            ),
            params,
        )
        return [dict(row) for row in result.mappings().all()]
