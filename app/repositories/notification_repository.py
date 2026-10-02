from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories._json import to_jsonb_param


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_delivery_schema(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS notification_deliveries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                review_id UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
                hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
                platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
                channel_code VARCHAR(100) NOT NULL,
                event_type VARCHAR(50) NOT NULL DEFAULT 'bad_review',
                delivery_status VARCHAR(30) NOT NULL DEFAULT 'pending',
                target_ref VARCHAR(255),
                external_message_id VARCHAR(255),
                attempt_count INTEGER NOT NULL DEFAULT 1,
                first_attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                sent_at TIMESTAMPTZ,
                error_message TEXT,
                request_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
                response_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
                metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid()",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS review_id UUID",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS hotel_id UUID",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS platform_id UUID",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS channel_code VARCHAR(100)",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS event_type VARCHAR(50) NOT NULL DEFAULT 'bad_review'",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS delivery_status VARCHAR(30) NOT NULL DEFAULT 'pending'",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS target_ref VARCHAR(255)",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS external_message_id VARCHAR(255)",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS first_attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS last_attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS error_message TEXT",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS request_payload JSONB NOT NULL DEFAULT '{}'::JSONB",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS response_payload JSONB NOT NULL DEFAULT '{}'::JSONB",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::JSONB",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
            "ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
            "UPDATE notification_deliveries SET id = gen_random_uuid() WHERE id IS NULL",
            "UPDATE notification_deliveries SET event_type = 'bad_review' WHERE event_type IS NULL OR btrim(event_type) = ''",
            "UPDATE notification_deliveries SET delivery_status = 'pending' WHERE delivery_status IS NULL OR btrim(delivery_status) = ''",
            "UPDATE notification_deliveries SET attempt_count = 1 WHERE attempt_count IS NULL OR attempt_count < 1",
            "UPDATE notification_deliveries SET first_attempted_at = COALESCE(first_attempted_at, created_at, NOW()) WHERE first_attempted_at IS NULL",
            "UPDATE notification_deliveries SET last_attempted_at = COALESCE(last_attempted_at, updated_at, created_at, NOW()) WHERE last_attempted_at IS NULL",
            "UPDATE notification_deliveries SET created_at = COALESCE(created_at, NOW()) WHERE created_at IS NULL",
            "UPDATE notification_deliveries SET updated_at = COALESCE(updated_at, last_attempted_at, created_at, NOW()) WHERE updated_at IS NULL",
            """
            WITH ranked AS (
                SELECT
                    ctid,
                    row_number() OVER (
                        PARTITION BY review_id, channel_code, event_type
                        ORDER BY
                            CASE WHEN delivery_status = 'sent' THEN 0 ELSE 1 END,
                            COALESCE(sent_at, last_attempted_at, updated_at, created_at, NOW()) DESC,
                            COALESCE(updated_at, created_at, NOW()) DESC
                    ) AS rn
                FROM notification_deliveries
                WHERE review_id IS NOT NULL
                  AND channel_code IS NOT NULL
                  AND event_type IS NOT NULL
            )
            DELETE FROM notification_deliveries nd
            USING ranked
            WHERE nd.ctid = ranked.ctid
              AND ranked.rn > 1
            """,
        ]

        for statement in statements:
            self.db.execute(text(statement))

    @staticmethod
    def _good_review_clause(good_min: float) -> str:
        return f"r.rating IS NOT NULL AND r.rating >= {float(good_min)}"

    @staticmethod
    def _bad_review_clause(average_min: float) -> str:
        return (
            f"((r.rating IS NOT NULL AND r.rating < {float(average_min)}) "
            "OR (r.rating IS NULL AND r.is_bad_review = TRUE))"
        )

    def _review_label_clause(self, review_label: str, *, average_min: float, good_min: float) -> str:
        bad_clause = self._bad_review_clause(average_min)
        good_clause = self._good_review_clause(good_min)
        if review_label == "bad":
            return bad_clause
        if review_label == "good":
            return good_clause
        if review_label == "all":
            return f"({bad_clause} OR {good_clause})"
        raise ValueError(f"Unsupported review_label: {review_label}")

    def get_bad_reviews_by_ids(
        self,
        *,
        review_ids: list[str],
        review_label: str = "bad",
        average_min: float,
        good_min: float,
    ) -> list[dict[str, Any]]:
        if not review_ids:
            return []

        query = text(
            """
            SELECT
                r.id::text AS id,
                r.hotel_id::text AS hotel_id,
                h.hotel_name,
                p.platform_code,
                CASE WHEN r.is_bad_review = TRUE THEN 'bad_review' ELSE 'good_review' END AS derived_event_type,
                CASE WHEN r.is_bad_review = TRUE THEN 'bad' ELSE 'good' END AS derived_review_label,
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
                r.updated_at
            FROM reviews r
            JOIN hotels h ON h.id = r.hotel_id
            JOIN platforms p ON p.id = r.platform_id
            WHERE r.id = ANY(CAST(:review_ids AS uuid[]))
              AND {self._review_label_clause(review_label, average_min=average_min, good_min=good_min)}
            ORDER BY r.reviewed_at DESC, r.created_at DESC
            """
        )
        rows = self.db.execute(query, {"review_ids": review_ids}).mappings().all()
        return [dict(row) for row in rows]

    def list_unnotified_bad_reviews(
        self,
        *,
        channel_code: str,
        event_type: str,
        review_label: str,
        hotel_id: str | None,
        platform_code: str | None,
        reviewed_from: datetime,
        average_min: float,
        good_min: float,
        include_sent: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        filters = [
            self._review_label_clause(
                review_label,
                average_min=average_min,
                good_min=good_min,
            ),
            "r.reviewed_at >= :reviewed_from",
        ]
        params: dict[str, Any] = {
            "channel_code": channel_code,
            "event_type": event_type,
            "reviewed_from": reviewed_from,
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
        if review_label == "all":
            not_exists_event_type_clause = (
                "nd.event_type = CASE WHEN r.is_bad_review = TRUE THEN 'bad_review' ELSE 'good_review' END"
            )
        else:
            not_exists_event_type_clause = "nd.event_type = :event_type"

        if include_sent:
            not_exists_delivery_clause = ""
        elif channel_code.strip().lower() == "larknoibo":
            not_exists_delivery_clause = """
                nd.review_id = r.id
                AND nd.channel_code = :channel_code
                AND nd.delivery_status = 'sent'
            """
        else:
            not_exists_delivery_clause = f"""
                nd.review_id = r.id
                AND nd.channel_code = :channel_code
                AND {not_exists_event_type_clause}
                AND nd.delivery_status = 'sent'
            """
        delivery_filter = ""
        if not_exists_delivery_clause:
            delivery_filter = f"""
              AND NOT EXISTS (
                  SELECT 1
                  FROM notification_deliveries nd
                  WHERE {not_exists_delivery_clause}
              )
            """

        query = text(
            f"""
            SELECT
                r.id::text AS id,
                r.hotel_id::text AS hotel_id,
                h.hotel_name,
                p.platform_code,
                CASE WHEN r.is_bad_review = TRUE THEN 'bad_review' ELSE 'good_review' END AS derived_event_type,
                CASE WHEN r.is_bad_review = TRUE THEN 'bad' ELSE 'good' END AS derived_review_label,
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
              {delivery_filter}
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
        event_type: str | None,
        delivery_status: str,
        target_ref: str | None,
        external_message_id: str | None,
        error_message: str | None,
        request_payload: dict[str, Any],
        response_payload: dict[str, Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        self.ensure_delivery_schema()
        if channel_code.strip().lower() == "larknoibo":
            update_sql = """
                UPDATE notification_deliveries
                SET
                    event_type = COALESCE(CAST(:event_type AS varchar), event_type),
                    delivery_status = CAST(:delivery_status AS varchar),
                    target_ref = CAST(:target_ref AS varchar),
                    external_message_id = CAST(:external_message_id AS varchar),
                    error_message = CAST(:error_message AS text),
                    request_payload = CAST(:request_payload AS jsonb),
                    response_payload = CAST(:response_payload AS jsonb),
                    metadata = CAST(:metadata AS jsonb),
                    attempt_count = COALESCE(attempt_count, 0) + 1,
                    last_attempted_at = NOW(),
                    sent_at = CASE
                        WHEN CAST(:delivery_status AS varchar) = 'sent' THEN NOW()
                        ELSE sent_at
                    END,
                    updated_at = NOW()
                WHERE review_id = CAST(:review_id AS uuid)
                  AND channel_code = CAST(:channel_code AS varchar)
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
            insert_sql = """
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
                    COALESCE(
                        CAST(:event_type AS varchar),
                        CASE
                            WHEN r.is_bad_review = TRUE THEN CAST('bad_review' AS varchar)
                            ELSE CAST('good_review' AS varchar)
                        END
                    ),
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
        else:
            update_sql = """
                UPDATE notification_deliveries
                SET
                    delivery_status = CAST(:delivery_status AS varchar),
                    target_ref = CAST(:target_ref AS varchar),
                    external_message_id = CAST(:external_message_id AS varchar),
                    error_message = CAST(:error_message AS text),
                    request_payload = CAST(:request_payload AS jsonb),
                    response_payload = CAST(:response_payload AS jsonb),
                    metadata = CAST(:metadata AS jsonb),
                    attempt_count = COALESCE(attempt_count, 0) + 1,
                    last_attempted_at = NOW(),
                    sent_at = CASE
                        WHEN CAST(:delivery_status AS varchar) = 'sent' THEN NOW()
                        ELSE sent_at
                    END,
                    updated_at = NOW()
                WHERE review_id = CAST(:review_id AS uuid)
                  AND channel_code = CAST(:channel_code AS varchar)
                  AND event_type = CAST(:event_type AS varchar)
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
            insert_sql = """
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
        update_result = self.db.execute(
            text(update_sql),
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
        updated_row = update_result.mappings().first()
        if updated_row is not None:
            return dict(updated_row)

        insert_result = self.db.execute(
            text(insert_sql),
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
        row = insert_result.mappings().first()
        if row is None:
            raise ValueError(f"Review not found: {review_id}")
        return dict(row)
