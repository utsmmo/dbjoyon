from sqlalchemy.orm import Session

from app.repositories.incident_repository import IncidentRepository
from app.repositories.review_category_repository import ReviewCategoryRepository
from app.repositories.hotel_repository import HotelRepository
from app.repositories.platform_repository import PlatformRepository
from app.repositories.review_metric_repository import ReviewMetricRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.sync_job_repository import SyncJobRepository
from app.schemas.sync import SyncReviewsRequest, SyncReviewsResponse
from app.services.link_normalizer import normalize_source_link
from app.services.platform_registry import get_review_mapper
from app.services.translation_service import TranslationService


class ReviewSyncService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.hotel_repository = HotelRepository(db)
        self.platform_repository = PlatformRepository(db)
        self.sync_job_repository = SyncJobRepository(db)
        self.review_repository = ReviewRepository(db)
        self.review_metric_repository = ReviewMetricRepository(db)
        self.review_category_repository = ReviewCategoryRepository(db)
        self.incident_repository = IncidentRepository(db)
        self.translation_service = TranslationService()

    def sync_reviews(
        self,
        *,
        platform_code: str,
        payload: SyncReviewsRequest,
    ) -> SyncReviewsResponse:
        platform = self.platform_repository.get_platform_by_code(platform_code)
        if platform is None:
            raise ValueError(f"Platform not found or inactive: {platform_code}")

        hotel = self.hotel_repository.get_hotel_by_id(payload.hotel_id)
        if hotel is None:
            raise ValueError(f"Hotel not found: {payload.hotel_id}")

        if payload.source_link_used:
            normalized_source_link = normalize_source_link(
                platform_code,
                payload.source_link_used,
            )
            source_links = (
                hotel.get("metadata", {}).get("source_links", {}).get(platform_code, [])
            )
            normalized_source_links = [
                normalize_source_link(platform_code, link) for link in source_links
            ]
            if normalized_source_link not in normalized_source_links:
                raise ValueError(
                    "source_link_used is not registered for this hotel and platform"
                )

        mapper = get_review_mapper(platform_code)
        sync_job_id = self.sync_job_repository.create_job(
            job_type="review_sync",
            target_type="reviews",
            hotel_id=payload.hotel_id,
            platform_id=platform["id"],
            hotel_platform_account_id=payload.hotel_platform_account_id,
            triggered_by=payload.triggered_by,
            request_payload=payload.model_dump(mode="json"),
        )

        inserted = 0
        updated = 0
        incidents_opened = 0
        stored_total_reviews_before_sync = self.review_repository.count_reviews(
            hotel_id=payload.hotel_id,
            platform_id=platform["id"],
        )

        try:
            if (
                payload.source_total_reviews is not None
                or payload.source_average_rating is not None
                or payload.source_rating_scale is not None
                or payload.source_review_url is not None
                or payload.source_metrics_payload
            ):
                self.review_metric_repository.upsert_current_metrics(
                    hotel_id=payload.hotel_id,
                    platform_id=platform["id"],
                    hotel_platform_account_id=payload.hotel_platform_account_id,
                    source_total_reviews=payload.source_total_reviews,
                    source_average_rating=payload.source_average_rating,
                    source_rating_scale=payload.source_rating_scale,
                    source_review_url=payload.source_review_url,
                    source_captured_at=payload.source_captured_at.isoformat()
                    if payload.source_captured_at
                    else None,
                    raw_payload=payload.source_metrics_payload,
                    metadata={"triggered_by": payload.triggered_by},
                )

            if payload.source_categories or payload.source_category_payload:
                self.review_category_repository.upsert_category_snapshot(
                    hotel_id=payload.hotel_id,
                    platform_id=platform["id"],
                    hotel_platform_account_id=payload.hotel_platform_account_id,
                    source_captured_at=payload.source_captured_at.isoformat()
                    if payload.source_captured_at
                    else None,
                    categories_payload=[
                        item.model_dump(mode="json")
                        for item in payload.source_categories
                    ],
                    raw_payload=payload.source_category_payload,
                    metadata={"triggered_by": payload.triggered_by},
                )

            for item in payload.reviews:
                normalized_review = mapper.normalize(item)
                normalized_review = self.translation_service.enrich_review_translation(normalized_review)
                upserted = self.review_repository.upsert_review(
                    hotel_id=payload.hotel_id,
                    platform_id=platform["id"],
                    hotel_platform_account_id=payload.hotel_platform_account_id,
                    review=normalized_review,
                )

                if upserted["inserted"]:
                    inserted += 1
                else:
                    updated += 1

                if upserted["is_bad_review"]:
                    opened = self.incident_repository.create_bad_review_incident(
                        hotel_id=payload.hotel_id,
                        review_id=upserted["id"],
                        title=f"Bad review detected from {platform_code}",
                        description=normalized_review.get("review_text") or normalized_review.get("review_title"),
                        metadata={
                            "severity": "high",
                            "platform_code": platform_code,
                            "external_review_id": normalized_review["external_review_id"],
                            "triggered_by": payload.triggered_by,
                        },
                    )
                    incidents_opened += int(opened)

            stored_total_reviews_after_sync = self.review_repository.count_reviews(
                hotel_id=payload.hotel_id,
                platform_id=platform["id"],
            )
            estimated_new_reviews_from_source = None
            if payload.source_total_reviews is not None:
                estimated_new_reviews_from_source = max(
                    payload.source_total_reviews - stored_total_reviews_before_sync,
                    0,
                )

            self.sync_job_repository.finish_job(
                sync_job_id=sync_job_id,
                status="success",
                records_fetched=len(payload.reviews),
                records_inserted=inserted,
                records_updated=updated,
                response_payload={
                    "platform_code": platform_code,
                        "fetched": len(payload.reviews),
                        "inserted": inserted,
                        "updated": updated,
                        "incidents_opened": incidents_opened,
                        "source_total_reviews": payload.source_total_reviews,
                        "source_average_rating": payload.source_average_rating,
                        "source_rating_scale": payload.source_rating_scale,
                        "source_review_url": payload.source_review_url,
                        "source_link_used": payload.source_link_used,
                        "source_captured_at": payload.source_captured_at.isoformat()
                        if payload.source_captured_at
                        else None,
                        "estimated_new_reviews_from_source": estimated_new_reviews_from_source,
                        "stored_total_reviews_before_sync": stored_total_reviews_before_sync,
                        "stored_total_reviews_after_sync": stored_total_reviews_after_sync,
                    },
                )
            self.db.commit()
        except Exception as exc:
            self.sync_job_repository.finish_job(
                sync_job_id=sync_job_id,
                status="failed",
                records_fetched=len(payload.reviews),
                records_inserted=inserted,
                records_updated=updated,
                response_payload={"platform_code": platform_code},
                error_message=str(exc),
            )
            self.db.rollback()
            raise

        return SyncReviewsResponse(
            sync_job_id=sync_job_id,
            hotel_id=payload.hotel_id,
            platform_code=platform_code,
            source_total_reviews=payload.source_total_reviews,
            source_average_rating=payload.source_average_rating,
            source_rating_scale=payload.source_rating_scale,
            source_review_url=payload.source_review_url,
            source_captured_at=payload.source_captured_at,
            estimated_new_reviews_from_source=estimated_new_reviews_from_source,
            stored_total_reviews_before_sync=stored_total_reviews_before_sync,
            stored_total_reviews_after_sync=stored_total_reviews_after_sync,
            fetched=len(payload.reviews),
            inserted=inserted,
            updated=updated,
            incidents_opened=incidents_opened,
            status="success",
        )
