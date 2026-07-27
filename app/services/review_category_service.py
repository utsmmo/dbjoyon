from sqlalchemy.orm import Session

from app.repositories.review_category_repository import ReviewCategoryRepository
from app.schemas.review_category import ReviewCategoryCurrentListResponse


class ReviewCategoryService:
    def __init__(self, db: Session) -> None:
        self.repository = ReviewCategoryRepository(db)

    def list_current_categories(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
    ) -> ReviewCategoryCurrentListResponse:
        items = self.repository.list_current_categories(
            hotel_id=hotel_id,
            platform_code=platform_code,
        )
        return ReviewCategoryCurrentListResponse(items=items, total=len(items))
