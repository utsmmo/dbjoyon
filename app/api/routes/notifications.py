from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Literal

from app.api.deps import db_session
from app.schemas.notification import (
    LarkBadReviewSendRequest,
    LarkBadReviewSendResponse,
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
    recent_days: int = Query(default=10, ge=1, le=60),
    include_sent: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_session),
) -> UnnotifiedBadReviewListResponse:
    service = NotificationService(db)
    return service.list_unnotified_bad_reviews(
        review_label="bad",
        channel_code=channel_code,
        event_type=event_type,
        hotel_id=hotel_id,
        platform_code=platform_code,
        recent_days=recent_days,
        include_sent=include_sent,
        limit=limit,
        offset=offset,
    )


@router.get("/reviews/unnotified", response_model=UnnotifiedBadReviewListResponse)
def list_unnotified_reviews(
    review_label: Literal["bad", "good", "all"] = Query(default="bad"),
    channel_code: str = Query(..., min_length=1, max_length=100),
    event_type: str | None = Query(default=None, min_length=1, max_length=50),
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    recent_days: int = Query(default=10, ge=1, le=60),
    include_sent: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_session),
) -> UnnotifiedBadReviewListResponse:
    service = NotificationService(db)
    resolved_event_type = event_type or ("mixed_review" if review_label == "all" else f"{review_label}_review")
    return service.list_unnotified_bad_reviews(
        review_label=review_label,
        channel_code=channel_code,
        event_type=resolved_event_type,
        hotel_id=hotel_id,
        platform_code=platform_code,
        recent_days=recent_days,
        include_sent=include_sent,
        limit=limit,
        offset=offset,
    )


@router.get("/reviews/larknoibo/unnotified", response_model=UnnotifiedBadReviewListResponse)
def list_unnotified_reviews_for_larknoibo(
    review_label: Literal["bad", "good", "all"] = Query(default="all"),
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    recent_days: int = Query(default=10, ge=1, le=60),
    include_sent: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_session),
) -> UnnotifiedBadReviewListResponse:
    service = NotificationService(db)
    resolved_event_type = "mixed_review" if review_label == "all" else f"{review_label}_review"
    return service.list_unnotified_bad_reviews(
        review_label=review_label,
        channel_code="larknoibo",
        event_type=resolved_event_type,
        hotel_id=hotel_id,
        platform_code=platform_code,
        recent_days=recent_days,
        include_sent=include_sent,
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


@router.post(
    "/notifications/lark/bad-reviews/send",
    response_model=LarkBadReviewSendResponse,
    status_code=status.HTTP_200_OK,
)
def send_bad_reviews_to_lark(
    payload: LarkBadReviewSendRequest,
    db: Session = Depends(db_session),
) -> LarkBadReviewSendResponse:
    service = NotificationService(db)
    try:
        payload.review_label = "bad"
        if not payload.event_type:
            payload.event_type = "bad_review"
        return service.send_bad_reviews_to_lark(payload)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/notifications/lark/reviews/send",
    response_model=LarkBadReviewSendResponse,
    status_code=status.HTTP_200_OK,
)
def send_reviews_to_lark(
    payload: LarkBadReviewSendRequest,
    db: Session = Depends(db_session),
) -> LarkBadReviewSendResponse:
    service = NotificationService(db)
    try:
        return service.send_bad_reviews_to_lark(payload)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/notifications/larknoibo/reviews/send",
    response_model=LarkBadReviewSendResponse,
    status_code=status.HTTP_200_OK,
)
def send_reviews_to_larknoibo(
    payload: LarkBadReviewSendRequest,
    db: Session = Depends(db_session),
) -> LarkBadReviewSendResponse:
    service = NotificationService(db)
    try:
        payload.channel_code = "larknoibo"
        if payload.review_label == "all" and not payload.event_type:
            payload.event_type = "mixed_review"
        return service.send_bad_reviews_to_lark(payload)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
