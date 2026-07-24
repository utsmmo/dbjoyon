from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.review import ReviewListResponse, ReviewStatsListResponse
from app.services.review_query_service import ReviewQueryService

router = APIRouter(tags=["reviews"])


@router.get("/reviews", response_model=ReviewListResponse)
def list_reviews(
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    is_bad_review: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_session),
) -> ReviewListResponse:
    service = ReviewQueryService(db)
    return service.list_reviews(
        hotel_id=hotel_id,
        platform_code=platform_code,
        is_bad_review=is_bad_review,
        limit=limit,
        offset=offset,
    )


@router.get("/reviews/bad", response_model=ReviewListResponse)
def list_bad_reviews(
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_session),
) -> ReviewListResponse:
    service = ReviewQueryService(db)
    return service.list_reviews(
        hotel_id=hotel_id,
        platform_code=platform_code,
        is_bad_review=True,
        limit=limit,
        offset=offset,
    )


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
