from datetime import date, datetime

from sqlalchemy.orm import Session

from app.repositories.review_analytics_repository import ReviewAnalyticsRepository
from app.schemas.review_analytics import (
    ReviewCountryBreakdownResponse,
    ReviewDailyTrendResponse,
    ReviewHotelBreakdownResponse,
    ReviewScoreBucketsResponse,
    ReviewSummaryAggregateResponse,
)


class ReviewAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.repository = ReviewAnalyticsRepository(db)

    def get_summary(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
        reviewer_country_code: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> ReviewSummaryAggregateResponse:
        date_from_value = self._to_date(date_from)
        date_to_value = self._to_date(date_to)
        self._validate_date_range(date_from_value, date_to_value)

        if date_from_value is None and date_to_value is None and reviewer_country_code is None:
            payload = self.repository.get_summary_current(
                hotel_id=hotel_id,
                platform_code=platform_code,
            )
        else:
            payload = self.repository.get_summary_daily(
                hotel_id=hotel_id,
                platform_code=platform_code,
                reviewer_country_code=reviewer_country_code,
                date_from=date_from_value,
                date_to=date_to_value,
            )

        total_reviews = int(payload.get("total_reviews") or 0)
        bad_reviews = int(payload.get("bad_reviews") or 0)
        bad_review_ratio = (bad_reviews / total_reviews) if total_reviews > 0 else 0.0

        return ReviewSummaryAggregateResponse(
            hotel_id=payload.get("hotel_id") or hotel_id,
            platform_code=payload.get("platform_code") or platform_code,
            reviewer_country_code=reviewer_country_code.upper() if reviewer_country_code else None,
            date_from=date_from_value,
            date_to=date_to_value,
            total_reviews=total_reviews,
            bad_reviews=bad_reviews,
            bad_review_ratio=round(bad_review_ratio, 4),
            avg_rating=payload.get("avg_rating"),
            positive_reviews=payload.get("positive_reviews"),
            neutral_reviews=payload.get("neutral_reviews"),
            negative_reviews=payload.get("negative_reviews"),
            mixed_reviews=payload.get("mixed_reviews"),
            latest_reviewed_at=payload.get("latest_reviewed_at"),
            latest_source_updated_at=payload.get("latest_source_updated_at"),
            source_total_reviews=payload.get("source_total_reviews"),
            source_average_rating=payload.get("source_average_rating"),
            source_rating_scale=payload.get("source_rating_scale"),
            last_aggregated_at=payload.get("last_aggregated_at"),
        )

    def get_country_breakdown(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        limit: int,
    ) -> ReviewCountryBreakdownResponse:
        date_from_value = self._to_date(date_from)
        date_to_value = self._to_date(date_to)
        self._validate_required_date_range(date_from_value, date_to_value)

        items = self.repository.list_country_breakdown(
            hotel_id=hotel_id,
            platform_code=platform_code,
            date_from=date_from_value,
            date_to=date_to_value,
            limit=limit,
        )
        return ReviewCountryBreakdownResponse(items=items, total=len(items))

    def get_hotel_breakdown(
        self,
        *,
        platform_code: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        sort_by: str,
        sort_order: str,
        limit: int,
    ) -> ReviewHotelBreakdownResponse:
        allowed_sort_by = {"total_reviews", "bad_reviews", "avg_rating", "latest_reviewed_at", "hotel_name"}
        allowed_sort_order = {"asc", "desc"}
        date_from_value = self._to_date(date_from)
        date_to_value = self._to_date(date_to)

        self._validate_required_date_range(date_from_value, date_to_value)
        if sort_by not in allowed_sort_by:
            raise ValueError(
                "sort_by must be one of: total_reviews, bad_reviews, avg_rating, latest_reviewed_at, hotel_name"
            )
        if sort_order.lower() not in allowed_sort_order:
            raise ValueError("sort_order must be either 'asc' or 'desc'")

        items = self.repository.list_hotel_breakdown(
            platform_code=platform_code,
            date_from=date_from_value,
            date_to=date_to_value,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
        )
        return ReviewHotelBreakdownResponse(items=items, total=len(items))

    def get_score_buckets(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
        reviewer_country_code: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> ReviewScoreBucketsResponse:
        if reviewer_country_code:
            raise ValueError("reviewer_country_code is not supported yet for score buckets in phase 1")

        date_from_value = self._to_date(date_from)
        date_to_value = self._to_date(date_to)
        self._validate_required_date_range(date_from_value, date_to_value)

        items = self.repository.list_score_buckets(
            hotel_id=hotel_id,
            platform_code=platform_code,
            date_from=date_from_value,
            date_to=date_to_value,
        )
        return ReviewScoreBucketsResponse(items=items, total=len(items))

    def get_daily_trend(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> ReviewDailyTrendResponse:
        date_from_value = self._to_date(date_from)
        date_to_value = self._to_date(date_to)
        self._validate_required_date_range(date_from_value, date_to_value)

        items = self.repository.list_daily_trend(
            hotel_id=hotel_id,
            platform_code=platform_code,
            date_from=date_from_value,
            date_to=date_to_value,
        )
        return ReviewDailyTrendResponse(items=items, total=len(items))

    @staticmethod
    def _to_date(value: datetime | None) -> date | None:
        if value is None:
            return None
        return value.date()

    @staticmethod
    def _validate_date_range(date_from: date | None, date_to: date | None) -> None:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise ValueError("date_from must be less than or equal to date_to")

    @classmethod
    def _validate_required_date_range(cls, date_from: date | None, date_to: date | None) -> None:
        if (date_from is None) != (date_to is None):
            raise ValueError("date_from and date_to must be provided together")
        if date_from is None or date_to is None:
            raise ValueError("date_from and date_to are required in phase 1")
        cls._validate_date_range(date_from, date_to)
