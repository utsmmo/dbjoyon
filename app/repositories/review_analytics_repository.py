from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class ReviewAnalyticsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary_current(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
    ) -> dict[str, Any]:
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
                    CASE
                        WHEN COUNT(DISTINCT m.hotel_id) = 1 THEN (ARRAY_AGG(DISTINCT m.hotel_id::text))[1]
                        ELSE NULL
                    END AS hotel_id,
                    CASE
                        WHEN COUNT(DISTINCT p.platform_code) = 1 THEN (ARRAY_AGG(DISTINCT p.platform_code))[1]
                        ELSE NULL
                    END AS platform_code,
                    COALESCE(SUM(m.total_reviews), 0)::int AS total_reviews,
                    COALESCE(SUM(m.bad_reviews), 0)::int AS bad_reviews,
                    CASE
                        WHEN COALESCE(SUM(m.total_reviews), 0) = 0 THEN NULL
                        ELSE ROUND(
                            SUM(COALESCE(m.avg_rating, 0) * m.total_reviews)
                            / NULLIF(SUM(m.total_reviews), 0),
                            4
                        )::float8
                    END AS avg_rating,
                    COALESCE(SUM(m.positive_reviews), 0)::int AS positive_reviews,
                    COALESCE(SUM(m.neutral_reviews), 0)::int AS neutral_reviews,
                    COALESCE(SUM(m.negative_reviews), 0)::int AS negative_reviews,
                    COALESCE(SUM(m.mixed_reviews), 0)::int AS mixed_reviews,
                    MAX(m.latest_reviewed_at) AS latest_reviewed_at,
                    MAX(m.latest_source_updated_at) AS latest_source_updated_at,
                    CASE
                        WHEN COUNT(*) = 1 THEN MAX(m.source_total_reviews)
                        ELSE NULL
                    END::int AS source_total_reviews,
                    CASE
                        WHEN COUNT(*) = 1 THEN MAX(m.source_average_rating)::float8
                        ELSE NULL
                    END AS source_average_rating,
                    CASE
                        WHEN COUNT(*) = 1 THEN MAX(m.source_rating_scale)::float8
                        ELSE NULL
                    END AS source_rating_scale,
                    MAX(m.last_aggregated_at) AS last_aggregated_at
                FROM review_dashboard_current_metrics m
                JOIN platforms p ON p.id = m.platform_id
                WHERE {where_clause}
                """
            ),
            params,
        )
        row = result.mappings().one()
        return dict(row)

    def get_summary_daily(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
        reviewer_country_code: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> dict[str, Any]:
        if reviewer_country_code:
            return self._get_summary_daily_by_country(
                hotel_id=hotel_id,
                platform_code=platform_code,
                reviewer_country_code=reviewer_country_code,
                date_from=date_from,
                date_to=date_to,
            )

        filters = ["1 = 1"]
        params: dict[str, Any] = {}

        if hotel_id:
            filters.append("m.hotel_id = CAST(:hotel_id AS uuid)")
            params["hotel_id"] = hotel_id
        if platform_code:
            filters.append("p.platform_code = :platform_code")
            params["platform_code"] = platform_code
        if date_from:
            filters.append("m.metric_date >= :date_from")
            params["date_from"] = date_from
        if date_to:
            filters.append("m.metric_date <= :date_to")
            params["date_to"] = date_to

        where_clause = " AND ".join(filters)
        result = self.db.execute(
            text(
                f"""
                SELECT
                    CASE
                        WHEN COUNT(DISTINCT m.hotel_id) = 1 THEN (ARRAY_AGG(DISTINCT m.hotel_id::text))[1]
                        ELSE NULL
                    END AS hotel_id,
                    CASE
                        WHEN COUNT(DISTINCT p.platform_code) = 1 THEN (ARRAY_AGG(DISTINCT p.platform_code))[1]
                        ELSE NULL
                    END AS platform_code,
                    COALESCE(SUM(m.total_reviews), 0)::int AS total_reviews,
                    COALESCE(SUM(m.bad_reviews), 0)::int AS bad_reviews,
                    CASE
                        WHEN COALESCE(SUM(m.total_reviews), 0) = 0 THEN NULL
                        ELSE ROUND(
                            SUM(COALESCE(m.avg_rating, 0) * m.total_reviews)
                            / NULLIF(SUM(m.total_reviews), 0),
                            4
                        )::float8
                    END AS avg_rating,
                    COALESCE(SUM(m.positive_reviews), 0)::int AS positive_reviews,
                    COALESCE(SUM(m.neutral_reviews), 0)::int AS neutral_reviews,
                    COALESCE(SUM(m.negative_reviews), 0)::int AS negative_reviews,
                    COALESCE(SUM(m.mixed_reviews), 0)::int AS mixed_reviews,
                    MAX(m.latest_reviewed_at) AS latest_reviewed_at,
                    MAX(m.latest_source_updated_at) AS latest_source_updated_at
                FROM review_dashboard_daily_metrics m
                JOIN platforms p ON p.id = m.platform_id
                WHERE {where_clause}
                """
            ),
            params,
        )
        return dict(result.mappings().one())

    def _get_summary_daily_by_country(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
        reviewer_country_code: str,
        date_from: date | None,
        date_to: date | None,
    ) -> dict[str, Any]:
        filters = ["1 = 1"]
        params: dict[str, Any] = {"reviewer_country_code": reviewer_country_code.upper()}

        if hotel_id:
            filters.append("m.hotel_id = CAST(:hotel_id AS uuid)")
            params["hotel_id"] = hotel_id
        if platform_code:
            filters.append("p.platform_code = :platform_code")
            params["platform_code"] = platform_code
        if date_from:
            filters.append("m.metric_date >= :date_from")
            params["date_from"] = date_from
        if date_to:
            filters.append("m.metric_date <= :date_to")
            params["date_to"] = date_to

        filters.append("m.reviewer_country_code = :reviewer_country_code")
        where_clause = " AND ".join(filters)
        result = self.db.execute(
            text(
                f"""
                SELECT
                    CASE
                        WHEN COUNT(DISTINCT m.hotel_id) = 1 THEN (ARRAY_AGG(DISTINCT m.hotel_id::text))[1]
                        ELSE NULL
                    END AS hotel_id,
                    CASE
                        WHEN COUNT(DISTINCT p.platform_code) = 1 THEN (ARRAY_AGG(DISTINCT p.platform_code))[1]
                        ELSE NULL
                    END AS platform_code,
                    COALESCE(SUM(m.total_reviews), 0)::int AS total_reviews,
                    COALESCE(SUM(m.bad_reviews), 0)::int AS bad_reviews,
                    CASE
                        WHEN COALESCE(SUM(m.total_reviews), 0) = 0 THEN NULL
                        ELSE ROUND(
                            SUM(COALESCE(m.avg_rating, 0) * m.total_reviews)
                            / NULLIF(SUM(m.total_reviews), 0),
                            4
                        )::float8
                    END AS avg_rating
                FROM review_dashboard_daily_country_metrics m
                JOIN platforms p ON p.id = m.platform_id
                WHERE {where_clause}
                """
            ),
            params,
        )
        return dict(result.mappings().one())

    def list_country_breakdown(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
        date_from: date | None,
        date_to: date | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        filters = ["1 = 1"]
        params: dict[str, Any] = {"limit": limit}

        if hotel_id:
            filters.append("m.hotel_id = CAST(:hotel_id AS uuid)")
            params["hotel_id"] = hotel_id
        if platform_code:
            filters.append("p.platform_code = :platform_code")
            params["platform_code"] = platform_code
        if date_from:
            filters.append("m.metric_date >= :date_from")
            params["date_from"] = date_from
        if date_to:
            filters.append("m.metric_date <= :date_to")
            params["date_to"] = date_to

        where_clause = " AND ".join(filters)
        result = self.db.execute(
            text(
                f"""
                SELECT
                    m.reviewer_country_code,
                    COALESCE(SUM(m.total_reviews), 0)::int AS total_reviews,
                    COALESCE(SUM(m.bad_reviews), 0)::int AS bad_reviews,
                    CASE
                        WHEN COALESCE(SUM(m.total_reviews), 0) = 0 THEN NULL
                        ELSE ROUND(
                            SUM(COALESCE(m.avg_rating, 0) * m.total_reviews)
                            / NULLIF(SUM(m.total_reviews), 0),
                            4
                        )::float8
                    END AS avg_rating
                FROM review_dashboard_daily_country_metrics m
                JOIN platforms p ON p.id = m.platform_id
                WHERE {where_clause}
                GROUP BY m.reviewer_country_code
                ORDER BY total_reviews DESC, m.reviewer_country_code
                LIMIT :limit
                """
            ),
            params,
        )
        return [dict(row) for row in result.mappings().all()]

    def list_hotel_breakdown(
        self,
        *,
        platform_code: str | None,
        date_from: date | None,
        date_to: date | None,
        sort_by: str,
        sort_order: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        filters = ["1 = 1"]
        params: dict[str, Any] = {"limit": limit}
        sort_expression_map = {
            "total_reviews": "total_reviews",
            "bad_reviews": "bad_reviews",
            "avg_rating": "avg_rating",
            "latest_reviewed_at": "latest_reviewed_at",
            "hotel_name": "hotel_name",
        }

        if platform_code:
            filters.append("p.platform_code = :platform_code")
            params["platform_code"] = platform_code
        if date_from:
            filters.append("m.metric_date >= :date_from")
            params["date_from"] = date_from
        if date_to:
            filters.append("m.metric_date <= :date_to")
            params["date_to"] = date_to

        sort_expression = sort_expression_map[sort_by]
        sort_order_sql = "ASC" if sort_order.lower() == "asc" else "DESC"
        where_clause = " AND ".join(filters)

        result = self.db.execute(
            text(
                f"""
                SELECT
                    h.id::text AS hotel_id,
                    h.hotel_name,
                    CASE WHEN COUNT(DISTINCT p.platform_code) = 1 THEN MIN(p.platform_code) ELSE NULL END AS platform_code,
                    COALESCE(SUM(m.total_reviews), 0)::int AS total_reviews,
                    COALESCE(SUM(m.bad_reviews), 0)::int AS bad_reviews,
                    CASE
                        WHEN COALESCE(SUM(m.total_reviews), 0) = 0 THEN NULL
                        ELSE ROUND(
                            SUM(COALESCE(m.avg_rating, 0) * m.total_reviews)
                            / NULLIF(SUM(m.total_reviews), 0),
                            4
                        )::float8
                    END AS avg_rating,
                    MAX(m.latest_reviewed_at) AS latest_reviewed_at
                FROM review_dashboard_daily_metrics m
                JOIN hotels h ON h.id = m.hotel_id
                JOIN platforms p ON p.id = m.platform_id
                WHERE {where_clause}
                GROUP BY h.id, h.hotel_name
                ORDER BY {sort_expression} {sort_order_sql} NULLS LAST, h.hotel_name
                LIMIT :limit
                """
            ),
            params,
        )
        return [dict(row) for row in result.mappings().all()]

    def list_score_buckets(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> list[dict[str, Any]]:
        filters = ["1 = 1"]
        params: dict[str, Any] = {}

        if hotel_id:
            filters.append("m.hotel_id = CAST(:hotel_id AS uuid)")
            params["hotel_id"] = hotel_id
        if platform_code:
            filters.append("p.platform_code = :platform_code")
            params["platform_code"] = platform_code
        if date_from:
            filters.append("m.metric_date >= :date_from")
            params["date_from"] = date_from
        if date_to:
            filters.append("m.metric_date <= :date_to")
            params["date_to"] = date_to

        where_clause = " AND ".join(filters)
        result = self.db.execute(
            text(
                f"""
                SELECT
                    m.bucket_code,
                    MIN(m.bucket_label) AS bucket_label,
                    MIN(m.rating_from)::float8 AS rating_from,
                    MAX(m.rating_to)::float8 AS rating_to,
                    COALESCE(SUM(m.review_count), 0)::int AS review_count,
                    COALESCE(SUM(m.bad_review_count), 0)::int AS bad_review_count
                FROM review_dashboard_daily_score_buckets m
                JOIN platforms p ON p.id = m.platform_id
                WHERE {where_clause}
                GROUP BY m.bucket_code
                ORDER BY MIN(m.rating_from), m.bucket_code
                """
            ),
            params,
        )
        return [dict(row) for row in result.mappings().all()]

    def list_daily_trend(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        filters = ["m.metric_date >= :date_from", "m.metric_date <= :date_to"]
        params: dict[str, Any] = {
            "date_from": date_from,
            "date_to": date_to,
        }

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
                    m.metric_date,
                    COALESCE(SUM(m.total_reviews), 0)::int AS total_reviews,
                    COALESCE(SUM(m.bad_reviews), 0)::int AS bad_reviews,
                    CASE
                        WHEN COALESCE(SUM(m.total_reviews), 0) = 0 THEN NULL
                        ELSE ROUND(
                            SUM(COALESCE(m.avg_rating, 0) * m.total_reviews)
                            / NULLIF(SUM(m.total_reviews), 0),
                            4
                        )::float8
                    END AS avg_rating,
                    COALESCE(SUM(m.positive_reviews), 0)::int AS positive_reviews,
                    COALESCE(SUM(m.neutral_reviews), 0)::int AS neutral_reviews,
                    COALESCE(SUM(m.negative_reviews), 0)::int AS negative_reviews,
                    COALESCE(SUM(m.mixed_reviews), 0)::int AS mixed_reviews
                FROM review_dashboard_daily_metrics m
                JOIN platforms p ON p.id = m.platform_id
                WHERE {where_clause}
                GROUP BY m.metric_date
                ORDER BY m.metric_date ASC
                """
            ),
            params,
        )
        return [dict(row) for row in result.mappings().all()]
