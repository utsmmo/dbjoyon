from datetime import datetime

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.db.session import SessionLocal
from app.schemas.review import (
    ReviewDeleteResponse,
    ReviewListResponse,
    ReviewStatsListResponse,
)
from app.services.review_admin_service import ReviewAdminService
from app.services.review_analytics_maintenance_service import (
    ReviewAnalyticsMaintenanceService,
)
from app.services.review_query_service import ReviewQueryService

router = APIRouter(tags=["reviews"])
logger = logging.getLogger(__name__)


def _rebuild_dashboard_analytics_background() -> None:
    db = SessionLocal()
    try:
        ReviewAnalyticsMaintenanceService(db).rebuild_dashboard_analytics()
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Background rebuild_dashboard_analytics failed after review delete")
    finally:
        db.close()


@router.get("/reviews", response_model=ReviewListResponse)
def list_reviews(
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    source_link: str | None = Query(default=None),
    is_bad_review: bool | None = Query(default=None),
    reviewer_country_code: str | None = Query(default=None),
    rating_min: float | None = Query(default=None),
    rating_max: float | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    q: str | None = Query(default=None),
    sort_by: str = Query(default="reviewed_at"),
    sort_order: str = Query(default="desc"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    hydrate_missing_translations: bool = Query(default=False),
    db: Session = Depends(db_session),
) -> ReviewListResponse:
    service = ReviewQueryService(db)
    try:
        return service.list_reviews(
            hotel_id=hotel_id,
            platform_code=platform_code,
            source_link=source_link,
            is_bad_review=is_bad_review,
            reviewer_country_code=reviewer_country_code,
            rating_min=rating_min,
            rating_max=rating_max,
            date_from=date_from,
            date_to=date_to,
            q=q,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
            hydrate_missing_translations=hydrate_missing_translations,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reviews/bad", response_model=ReviewListResponse)
def list_bad_reviews(
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    source_link: str | None = Query(default=None),
    reviewer_country_code: str | None = Query(default=None),
    rating_min: float | None = Query(default=None),
    rating_max: float | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    q: str | None = Query(default=None),
    sort_by: str = Query(default="reviewed_at"),
    sort_order: str = Query(default="desc"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    hydrate_missing_translations: bool = Query(default=False),
    db: Session = Depends(db_session),
) -> ReviewListResponse:
    service = ReviewQueryService(db)
    try:
        return service.list_reviews(
            hotel_id=hotel_id,
            platform_code=platform_code,
            source_link=source_link,
            is_bad_review=True,
            reviewer_country_code=reviewer_country_code,
            rating_min=rating_min,
            rating_max=rating_max,
            date_from=date_from,
            date_to=date_to,
            q=q,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
            hydrate_missing_translations=hydrate_missing_translations,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reviews/stats", response_model=ReviewStatsListResponse)
def list_review_stats(
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    db: Session = Depends(db_session),
) -> ReviewStatsListResponse:
    service = ReviewQueryService(db)
    return service.list_review_stats(
        hotel_id=hotel_id,
        platform_code=platform_code,
    )


@router.delete("/reviews", response_model=ReviewDeleteResponse)
def delete_reviews(
    background_tasks: BackgroundTasks,
    review_id: str | None = Query(default=None),
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    source_link: str | None = Query(default=None),
    db: Session = Depends(db_session),
) -> ReviewDeleteResponse:
    service = ReviewAdminService(db)
    try:
        response = service.delete_reviews(
            review_id=review_id,
            hotel_id=hotel_id,
            platform_code=platform_code,
            source_link=source_link,
        )
        background_tasks.add_task(_rebuild_dashboard_analytics_background)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
