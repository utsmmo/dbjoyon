from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.notification import (
    NotificationDeliveryUpsertRequest,
    NotificationDeliveryUpsertResponse,
    UnnotifiedBadReviewListResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(tags=["notifications"])


@router.get("/reviews/bad/unnotified", response_model=UnnotifiedBadReviewListResponse)
def list_unnotified_bad_reviews(
    channel_code: str = Query(..., min_length=1, max_length=100),
    event_type: str = Query(default="bad_review", min_length=1, max_length=50),
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_session),
) -> UnnotifiedBadReviewListResponse:
    service = NotificationService(db)
    return service.list_unnotified_bad_reviews(
        channel_code=channel_code,
        event_type=event_type,
        hotel_id=hotel_id,
        platform_code=platform_code,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/notifications/deliveries",
    response_model=NotificationDeliveryUpsertResponse,
    status_code=status.HTTP_200_OK,
)
def upsert_notification_delivery(
    payload: NotificationDeliveryUpsertRequest,
    db: Session = Depends(db_session),
) -> NotificationDeliveryUpsertResponse:
    service = NotificationService(db)
    try:
        return service.upsert_delivery(payload)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
