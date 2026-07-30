import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.hotel_repository import HotelRepository
from app.repositories.platform_repository import PlatformRepository
from app.repositories.review_category_repository import ReviewCategoryRepository
from app.repositories.review_metric_repository import ReviewMetricRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewDeleteResponse
from app.services.link_normalizer import normalize_source_link
from app.services.review_analytics_maintenance_service import (
    ReviewAnalyticsMaintenanceService,
)

logger = logging.getLogger(__name__)


class ReviewAdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.hotel_repository = HotelRepository(db)
        self.platform_repository = PlatformRepository(db)
        self.review_repository = ReviewRepository(db)
        self.review_metric_repository = ReviewMetricRepository(db)
        self.review_category_repository = ReviewCategoryRepository(db)
        self.analytics_maintenance_service = ReviewAnalyticsMaintenanceService(db)

    def delete_reviews(
        self,
        *,
        review_id: str | None,
        hotel_id: str | None,
        platform_code: str | None,
        source_link: str | None,
    ) -> ReviewDeleteResponse:
        if review_id:
            return self._delete_review_by_id(review_id=review_id)

        if not hotel_id or not platform_code:
            raise ValueError("hotel_id and platform_code are required when review_id is not provided")

        platform = self.platform_repository.get_platform_by_code(platform_code)
        if platform is None:
            raise ValueError(f"Platform not found or inactive: {platform_code}")

        hotel = self.hotel_repository.get_hotel_by_id(hotel_id)
        if hotel is None:
            raise ValueError(f"Hotel not found: {hotel_id}")

        resolved_source_link = None
        resolved_hotel_platform_account_id = None
        if source_link:
            resolved_source_link = normalize_source_link(platform_code, source_link)
            hotel_platform_account = (
                self.hotel_repository.get_hotel_platform_account_by_external_id(
                    hotel_id=hotel_id,
                    platform_id=platform["id"],
                    external_account_id=resolved_source_link,
                )
            )
            if hotel_platform_account is None:
                raise ValueError(
                    "source_link is not registered for this hotel and platform"
                )
            resolved_hotel_platform_account_id = hotel_platform_account["id"]

        try:
            deleted_reviews = self.review_repository.delete_reviews(
                hotel_id=hotel_id,
                platform_id=platform["id"],
                hotel_platform_account_id=resolved_hotel_platform_account_id,
            )

            deleted_review_metrics = 0
            deleted_category_snapshots = 0
            if resolved_hotel_platform_account_id is None:
                deleted_review_metrics = self.review_metric_repository.delete_current_metrics(
                    hotel_id=hotel_id,
                    platform_id=platform["id"],
                )
                deleted_category_snapshots = (
                    self.review_category_repository.delete_category_snapshots(
                        hotel_id=hotel_id,
                        platform_id=platform["id"],
                    )
                )

            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to delete reviews", extra={"hotel_id": hotel_id, "platform_code": platform_code})
            raise ValueError("database error while deleting reviews") from exc

        return ReviewDeleteResponse(
            review_id=None,
            hotel_id=hotel_id,
            platform_code=platform_code,
            source_link=resolved_source_link,
            deleted_reviews=deleted_reviews,
            deleted_review_metrics=deleted_review_metrics,
            deleted_category_snapshots=deleted_category_snapshots,
            status="success",
        )

    def _delete_review_by_id(
        self,
        *,
        review_id: str,
    ) -> ReviewDeleteResponse:
        review = self.review_repository.get_review_by_id(review_id=review_id)
        if review is None:
            raise ValueError(f"Review not found: {review_id}")

        try:
            deleted_reviews = self.review_repository.delete_review_by_id(review_id=review_id)
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to delete review by id", extra={"review_id": review_id})
            raise ValueError("database error while deleting review") from exc

        return ReviewDeleteResponse(
            review_id=review_id,
            hotel_id=review["hotel_id"],
            platform_code=review["platform_code"],
            source_link=review["source_link_used"],
            deleted_reviews=deleted_reviews,
            deleted_review_metrics=0,
            deleted_category_snapshots=0,
            status="success",
        )
