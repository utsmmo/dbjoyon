from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.review_analytics import (
    ReviewCountryBreakdownResponse,
    ReviewDailyTrendResponse,
    ReviewHotelBreakdownResponse,
    ReviewScoreBucketsResponse,
    ReviewSummaryAggregateResponse,
)
from app.services.review_analytics_service import ReviewAnalyticsService

router = APIRouter(tags=["review-analytics"])


@router.get("/reviews/summary", response_model=ReviewSummaryAggregateResponse)
def get_review_summary(
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    reviewer_country_code: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(db_session),
) -> ReviewSummaryAggregateResponse:
    service = ReviewAnalyticsService(db)
    try:
        return service.get_summary(
            hotel_id=hotel_id,
            platform_code=platform_code,
            reviewer_country_code=reviewer_country_code,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reviews/country-breakdown", response_model=ReviewCountryBreakdownResponse)
def get_country_breakdown(
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(db_session),
) -> ReviewCountryBreakdownResponse:
    service = ReviewAnalyticsService(db)
    try:
        return service.get_country_breakdown(
            hotel_id=hotel_id,
            platform_code=platform_code,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reviews/hotel-breakdown", response_model=ReviewHotelBreakdownResponse)
def get_hotel_breakdown(
    platform_code: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    sort_by: str = Query(default="total_reviews"),
    sort_order: str = Query(default="desc"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(db_session),
) -> ReviewHotelBreakdownResponse:
    service = ReviewAnalyticsService(db)
    try:
        return service.get_hotel_breakdown(
            platform_code=platform_code,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reviews/score-buckets", response_model=ReviewScoreBucketsResponse)
def get_score_buckets(
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    reviewer_country_code: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(db_session),
) -> ReviewScoreBucketsResponse:
    service = ReviewAnalyticsService(db)
    try:
        return service.get_score_buckets(
            hotel_id=hotel_id,
            platform_code=platform_code,
            reviewer_country_code=reviewer_country_code,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reviews/daily-trend", response_model=ReviewDailyTrendResponse)
def get_daily_trend(
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(db_session),
) -> ReviewDailyTrendResponse:
    service = ReviewAnalyticsService(db)
    try:
        return service.get_daily_trend(
            hotel_id=hotel_id,
            platform_code=platform_code,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
