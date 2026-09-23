from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories._json import to_jsonb_param


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_unnotified_bad_reviews(
        self,
        *,
        channel_code: str,
        event_type: str,
        hotel_id: str | None,
        platform_code: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        filters = ["r.is_bad_review = TRUE"]
        params: dict[str, Any] = {
            "channel_code": channel_code,
            "event_type": event_type,
            "limit": limit,
            "offset": offset,
        }

        if hotel_id:
            filters.append("r.hotel_id = CAST(:hotel_id AS uuid)")
            params["hotel_id"] = hotel_id
        if platform_code:
            filters.append("p.platform_code = :platform_code")
            params["platform_code"] = platform_code

        where_clause = " AND ".join(filters)

        query = text(
            f"""
            SELECT
                r.id::text AS id,
                r.hotel_id::text AS hotel_id,
                h.hotel_name,
                p.platform_code,
                r.external_review_id,
                r.reviewer_name,
                r.reviewer_country_code,
                r.rating,
                r.rating_scale,
                r.review_title,
                r.review_text,
                r.normalized_payload ->> 'translated_title_vi' AS translated_title_vi,
                r.normalized_payload ->> 'translated_text_vi' AS translated_text_vi,
                r.review_language,
                r.sentiment_label,
                r.is_bad_review,
                r.stay_date,
                r.reviewed_at,
                r.replied_at,
                r.source_updated_at,
                r.created_at,
                r.updated_at,
                COUNT(*) OVER() AS total_count
            FROM reviews r
            JOIN hotels h ON h.id = r.hotel_id
            JOIN platforms p ON p.id = r.platform_id
            WHERE {where_clause}
              AND NOT EXISTS (
                  SELECT 1
                  FROM notification_deliveries nd
                  WHERE nd.review_id = r.id
                    AND nd.channel_code = :channel_code
                    AND nd.event_type = :event_type
                    AND nd.delivery_status = 'sent'
              )
            ORDER BY r.reviewed_at DESC, r.created_at DESC
            LIMIT :limit OFFSET :offset
            """
        )
        rows = self.db.execute(query, params).mappings().all()
        total = int(rows[0]["total_count"]) if rows else 0
        items = [{k: v for k, v in row.items() if k != "total_count"} for row in rows]
        return items, total

    def upsert_delivery(
        self,
        *,
        review_id: str,
        channel_code: str,
        event_type: str,
        delivery_status: str,
        target_ref: str | None,
        external_message_id: str | None,
        error_message: str | None,
        request_payload: dict[str, Any],
        response_payload: dict[str, Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        result = self.db.execute(
            text(
                """
                INSERT INTO notification_deliveries (
                    review_id,
                    hotel_id,
                    platform_id,
                    channel_code,
                    event_type,
                    delivery_status,
                    target_ref,
                    external_message_id,
                    error_message,
                    request_payload,
                    response_payload,
                    metadata,
                    sent_at
                )
                SELECT
                    r.id,
                    r.hotel_id,
                    r.platform_id,
                    CAST(:channel_code AS varchar),
                    CAST(:event_type AS varchar),
                    CAST(:delivery_status AS varchar),
                    CAST(:target_ref AS varchar),
                    CAST(:external_message_id AS varchar),
                    CAST(:error_message AS text),
                    CAST(:request_payload AS jsonb),
                    CAST(:response_payload AS jsonb),
                    CAST(:metadata AS jsonb),
                    CASE WHEN CAST(:delivery_status AS varchar) = 'sent' THEN NOW() ELSE NULL END
                FROM reviews r
                WHERE r.id = CAST(:review_id AS uuid)
                ON CONFLICT (review_id, channel_code, event_type)
                DO UPDATE SET
                    delivery_status = EXCLUDED.delivery_status,
                    target_ref = EXCLUDED.target_ref,
                    external_message_id = EXCLUDED.external_message_id,
                    error_message = EXCLUDED.error_message,
                    request_payload = EXCLUDED.request_payload,
                    response_payload = EXCLUDED.response_payload,
                    metadata = EXCLUDED.metadata,
                    attempt_count = notification_deliveries.attempt_count + 1,
                    last_attempted_at = NOW(),
                    sent_at = CASE
                        WHEN EXCLUDED.delivery_status = 'sent' THEN NOW()
                        ELSE notification_deliveries.sent_at
                    END,
                    updated_at = NOW()
                RETURNING
                    id::text AS id,
                    review_id::text AS review_id,
                    channel_code,
                    event_type,
                    delivery_status,
                    attempt_count,
                    external_message_id,
                    sent_at,
                    updated_at
                """
            ),
            {
                "review_id": review_id,
                "channel_code": channel_code,
                "event_type": event_type,
                "delivery_status": delivery_status,
                "target_ref": target_ref,
                "external_message_id": external_message_id,
                "error_message": error_message,
                "request_payload": to_jsonb_param(request_payload),
                "response_payload": to_jsonb_param(response_payload),
                "metadata": to_jsonb_param(metadata),
            },
        )
        row = result.mappings().first()
        if row is None:
            raise ValueError(f"Review not found: {review_id}")
        return dict(row)
