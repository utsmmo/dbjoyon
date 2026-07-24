from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories._json import to_jsonb_param


class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_review(
        self,
        *,
        hotel_id: str,
        platform_id: str,
        hotel_platform_account_id: str | None,
        review: dict[str, Any],
    ) -> dict[str, Any]:
        result = self.db.execute(
            text(
                """
                INSERT INTO reviews (
                    hotel_id,
                    platform_id,
                    hotel_platform_account_id,
                    external_review_id,
                    review_url,
                    reviewer_name,
                    reviewer_country_code,
                    reviewer_profile,
                    rating,
                    rating_scale,
                    review_title,
                    review_text,
                    review_language,
                    sentiment_label,
                    is_bad_review,
                    stay_date,
                    reviewed_at,
                    replied_at,
                    source_created_at,
                    source_updated_at,
                    raw_payload,
                    normalized_payload,
                    metadata
                )
                VALUES (
                    CAST(:hotel_id AS uuid),
                    CAST(:platform_id AS uuid),
                    CAST(:hotel_platform_account_id AS uuid),
                    :external_review_id,
                    :review_url,
                    :reviewer_name,
                    :reviewer_country_code,
                    CAST(:reviewer_profile AS jsonb),
                    :rating,
                    :rating_scale,
                    :review_title,
                    :review_text,
                    :review_language,
                    :sentiment_label,
                    :is_bad_review,
                    :stay_date,
                    :reviewed_at,
                    :replied_at,
                    :source_created_at,
                    :source_updated_at,
                    CAST(:raw_payload AS jsonb),
                    CAST(:normalized_payload AS jsonb),
                    CAST(:metadata AS jsonb)
                )
                ON CONFLICT (hotel_id, platform_id, external_review_id)
                DO UPDATE SET
                    hotel_platform_account_id = EXCLUDED.hotel_platform_account_id,
                    review_url = EXCLUDED.review_url,
                    reviewer_name = EXCLUDED.reviewer_name,
                    reviewer_country_code = EXCLUDED.reviewer_country_code,
                    reviewer_profile = EXCLUDED.reviewer_profile,
                    rating = EXCLUDED.rating,
                    rating_scale = EXCLUDED.rating_scale,
                    review_title = EXCLUDED.review_title,
                    review_text = EXCLUDED.review_text,
                    review_language = EXCLUDED.review_language,
                    sentiment_label = EXCLUDED.sentiment_label,
                    is_bad_review = EXCLUDED.is_bad_review,
                    stay_date = EXCLUDED.stay_date,
                    reviewed_at = EXCLUDED.reviewed_at,
                    replied_at = EXCLUDED.replied_at,
                    source_created_at = EXCLUDED.source_created_at,
                    source_updated_at = EXCLUDED.source_updated_at,
                    raw_payload = EXCLUDED.raw_payload,
                    normalized_payload = EXCLUDED.normalized_payload,
                    metadata = EXCLUDED.metadata,
                    sync_version = reviews.sync_version + 1,
                    updated_at = NOW()
                RETURNING
                    id::text AS id,
                    (xmax = 0) AS inserted,
                    is_bad_review
                """
            ),
            {
                "hotel_id": hotel_id,
                "platform_id": platform_id,
                "hotel_platform_account_id": hotel_platform_account_id,
                **review,
                "reviewer_profile": to_jsonb_param(review.get("reviewer_profile")),
                "raw_payload": to_jsonb_param(review.get("raw_payload")),
                "normalized_payload": to_jsonb_param(review.get("normalized_payload")),
                "metadata": to_jsonb_param(review.get("metadata")),
            },
        )
        return dict(result.mappings().one())

    def list_reviews(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
        is_bad_review: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        filters = ["1 = 1"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if hotel_id:
            filters.append("r.hotel_id = CAST(:hotel_id AS uuid)")
            params["hotel_id"] = hotel_id
        if platform_code:
            filters.append("p.platform_code = :platform_code")
            params["platform_code"] = platform_code
        if is_bad_review is not None:
            filters.append("r.is_bad_review = :is_bad_review")
            params["is_bad_review"] = is_bad_review

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
            ORDER BY r.reviewed_at DESC, r.created_at DESC
            LIMIT :limit OFFSET :offset
            """
        )
        rows = self.db.execute(query, params).mappings().all()
        total = int(rows[0]["total_count"]) if rows else 0
        items = [{k: v for k, v in row.items() if k != "total_count"} for row in rows]
        return items, total

    def count_reviews(
        self,
        *,
        hotel_id: str,
        platform_id: str,
    ) -> int:
        result = self.db.execute(
            text(
                """
                SELECT COUNT(*) AS total_reviews
                FROM reviews
                WHERE hotel_id = CAST(:hotel_id AS uuid)
                  AND platform_id = CAST(:platform_id AS uuid)
                """
            ),
            {
                "hotel_id": hotel_id,
                "platform_id": platform_id,
            },
        )
        return int(result.scalar_one())

    def list_review_stats(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
    ) -> list[dict[str, Any]]:
        filters = ["1 = 1"]
        params: dict[str, Any] = {}

        if hotel_id:
            filters.append("r.hotel_id = CAST(:hotel_id AS uuid)")
            params["hotel_id"] = hotel_id

        if platform_code:
            filters.append("p.platform_code = :platform_code")
            params["platform_code"] = platform_code

        where_clause = " AND ".join(filters)

        result = self.db.execute(
            text(
                f"""
                SELECT
                    r.hotel_id::text AS hotel_id,
                    p.platform_code,
                    COUNT(*)::int AS total_reviews,
                    COUNT(*) FILTER (WHERE r.is_bad_review = TRUE)::int AS bad_reviews,
                    MAX(r.reviewed_at) AS latest_reviewed_at,
                    MAX(r.source_updated_at) AS latest_source_updated_at
                FROM reviews r
                JOIN hotels h ON h.id = r.hotel_id
                JOIN platforms p ON p.id = r.platform_id
                WHERE {where_clause}
                GROUP BY r.hotel_id, p.platform_code
                ORDER BY r.hotel_id, p.platform_code
                """
            ),
            params,
        )
        return [dict(row) for row in result.mappings().all()]

    def update_review_translations(
        self,
        *,
        review_id: str,
        translated_title_vi: str | None,
        translated_text_vi: str | None,
        translation_provider: str | None,
        translation_target_language: str | None,
        translation_detected_source_language: str | None,
    ) -> None:
        self.db.execute(
            text(
                """
                UPDATE reviews
                SET
                    normalized_payload = COALESCE(normalized_payload, '{}'::jsonb) ||
                        jsonb_strip_nulls(
                            jsonb_build_object(
                                'translated_title_vi', :translated_title_vi,
                                'translated_text_vi', :translated_text_vi,
                                'translation_provider', :translation_provider,
                                'translation_target_language', :translation_target_language,
                                'translation_detected_source_language', :translation_detected_source_language
                            )
                        ),
                    updated_at = NOW()
                WHERE id = CAST(:review_id AS uuid)
                """
            ),
            {
                "review_id": review_id,
                "translated_title_vi": translated_title_vi,
                "translated_text_vi": translated_text_vi,
                "translation_provider": translation_provider,
                "translation_target_language": translation_target_language,
                "translation_detected_source_language": translation_detected_source_language,
            },
        )

    def update_review_bad_flag(
        self,
        *,
        review_id: str,
        is_bad_review: bool,
    ) -> None:
        self.db.execute(
            text(
                """
                UPDATE reviews
                SET
                    is_bad_review = :is_bad_review,
                    updated_at = NOW()
                WHERE id = CAST(:review_id AS uuid)
                """
            ),
            {
                "review_id": review_id,
                "is_bad_review": is_bad_review,
            },
        )

    def list_google_sheet_rows(
        self,
        *,
        hotel_id: str,
    ) -> list[dict[str, Any]]:
        result = self.db.execute(
            text(
                """
                SELECT
                    r.id::text AS review_id,
                    h.hotel_name,
                    r.reviewed_at,
                    r.reviewer_name,
                    r.reviewer_country_code,
                    r.rating::float8 AS rating,
                    r.is_bad_review,
                    r.review_title,
                    r.review_text,
                    r.review_language,
                    r.normalized_payload ->> 'translated_title_vi' AS translated_title_vi,
                    r.normalized_payload ->> 'translated_text_vi' AS translated_text_vi
                FROM reviews r
                JOIN hotels h ON h.id = r.hotel_id
                WHERE r.hotel_id = CAST(:hotel_id AS uuid)
                ORDER BY r.reviewed_at DESC, r.created_at DESC
                """
            ),
            {"hotel_id": hotel_id},
        )
        return [dict(row) for row in result.mappings().all()]
