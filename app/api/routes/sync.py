import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.db.session import SessionLocal
from app.schemas.sync import SyncReviewsRequest, SyncReviewsResponse
from app.services.review_analytics_maintenance_service import (
    ReviewAnalyticsMaintenanceService,
)
from app.services.sync_service import ReviewSyncService

router = APIRouter(tags=["sync"])
logger = logging.getLogger(__name__)


def _rebuild_dashboard_analytics_background() -> None:
    db = SessionLocal()
    try:
        ReviewAnalyticsMaintenanceService(db).rebuild_dashboard_analytics()
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Background rebuild_dashboard_analytics failed")
    finally:
        db.close()


@router.post(
    "/sync/reviews/{platform_code}",
    response_model=SyncReviewsResponse,
    status_code=status.HTTP_200_OK,
)
def sync_reviews(
    platform_code: str,
    payload: SyncReviewsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(db_session),
) -> SyncReviewsResponse:
    service = ReviewSyncService(db)

    try:
        response = service.sync_reviews(platform_code=platform_code, payload=payload)
        background_tasks.add_task(_rebuild_dashboard_analytics_background)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
