from sqlalchemy.orm import Session

from app.repositories.review_metric_repository import ReviewMetricRepository
from app.schemas.review_metric import ReviewMetricListResponse


class ReviewMetricService:
    def __init__(self, db: Session) -> None:
        self.review_metric_repository = ReviewMetricRepository(db)

    def list_current_metrics(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
    ) -> ReviewMetricListResponse:
        items = self.review_metric_repository.list_current_metrics(
            hotel_id=hotel_id,
            platform_code=platform_code,
        )
        return ReviewMetricListResponse(items=items, total=len(items))
