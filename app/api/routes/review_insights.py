from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.review_insight import ReviewInsightRequest, ReviewInsightResponse
from app.services.review_insight_service import ReviewInsightService

router = APIRouter(tags=["review-insights"])


@router.post("/review-insights", response_model=ReviewInsightResponse)
def generate_review_insights(
    payload: ReviewInsightRequest,
    db: Session = Depends(db_session),
) -> ReviewInsightResponse:
    service = ReviewInsightService(db)
    try:
        return service.generate(payload)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
