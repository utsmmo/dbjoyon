from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.sync import SyncReviewsRequest, SyncReviewsResponse
from app.services.sync_service import ReviewSyncService

router = APIRouter(tags=["sync"])


@router.post(
    "/sync/reviews/{platform_code}",
    response_model=SyncReviewsResponse,
    status_code=status.HTTP_200_OK,
)
def sync_reviews(
    platform_code: str,
    payload: SyncReviewsRequest,
    db: Session = Depends(db_session),
) -> SyncReviewsResponse:
    service = ReviewSyncService(db)

    try:
        return service.sync_reviews(platform_code=platform_code, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
