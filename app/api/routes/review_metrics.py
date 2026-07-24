from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.review_metric import ReviewMetricListResponse
from app.services.review_metric_service import ReviewMetricService

router = APIRouter(tags=["review-metrics"])


@router.get("/review-metrics/current", response_model=ReviewMetricListResponse)
def list_current_review_metrics(
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    db: Session = Depends(db_session),
) -> ReviewMetricListResponse:
    service = ReviewMetricService(db)
    return service.list_current_metrics(
        hotel_id=hotel_id,
        platform_code=platform_code,
    )
