from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.review_category import ReviewCategoryCurrentListResponse
from app.services.review_category_service import ReviewCategoryService

router = APIRouter(tags=["review-categories"])


@router.get("/review-categories/current", response_model=ReviewCategoryCurrentListResponse)
def list_current_review_categories(
    hotel_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    db: Session = Depends(db_session),
) -> ReviewCategoryCurrentListResponse:
    service = ReviewCategoryService(db)
    return service.list_current_categories(
        hotel_id=hotel_id,
        platform_code=platform_code,
    )
