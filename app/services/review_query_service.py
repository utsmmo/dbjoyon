from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.platform_repository import PlatformRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewListResponse, ReviewStatsListResponse
from app.services.review_rating_service import ReviewRatingService
from app.services.translation_service import TranslationService


class ReviewQueryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.review_repository = ReviewRepository(db)
        self.platform_repository = PlatformRepository(db)
        self.translation_service = TranslationService()
        self.review_rating_service = ReviewRatingService(db)

    def list_reviews(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
        source_link: str | None,
        review_status: str | None,
        is_bad_review: bool | None,
        reviewer_country_code: str | None,
        rating_min: float | None,
        rating_max: float | None,
        date_from: datetime | None,
        date_to: datetime | None,
        q: str | None,
        sort_by: str,
        sort_order: str,
        limit: int,
        offset: int,
        hydrate_missing_translations: bool = False,
    ) -> ReviewListResponse:
        self._validate_review_filters(
            review_status=review_status,
            rating_min=rating_min,
            rating_max=rating_max,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        rating_rules = self.review_rating_service.load_rules()
        items, total = self.review_repository.list_reviews(
            hotel_id=hotel_id,
            platform_code=platform_code,
            source_link=source_link,
            review_status=review_status,
            average_min=rating_rules.average_min,
            good_min=rating_rules.good_min,
            is_bad_review=is_bad_review,
            reviewer_country_code=reviewer_country_code,
            rating_min=rating_min,
            rating_max=rating_max,
            date_from=date_from,
            date_to=date_to,
            q=q,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )
        items = self._normalize_review_items(items, rating_rules=rating_rules)
        if hydrate_missing_translations:
            items = self._hydrate_missing_translations(items)
        return ReviewListResponse(items=items, total=total, limit=limit, offset=offset)

    def list_review_stats(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
    ) -> ReviewStatsListResponse:
        items = self.review_repository.list_review_stats(
            hotel_id=hotel_id,
            platform_code=platform_code,
        )
        return ReviewStatsListResponse(items=items, total=len(items))

    def _hydrate_missing_translations(self, items: list[dict]) -> list[dict]:
        changed = False

        for item in items:
            try:
                if self._has_translation(item):
                    continue

                review_title = item.get("review_title")
                review_text = item.get("review_text")
                if not review_title and not review_text:
                    continue

                enriched = self.translation_service.enrich_review_translation(
                    {
                        "review_title": review_title,
                        "review_text": review_text,
                        "review_language": item.get("review_language"),
                        "normalized_payload": {},
                    }
                )
                normalized_payload = enriched.get("normalized_payload") or {}
                translated_title_vi = normalized_payload.get("translated_title_vi")
                translated_text_vi = normalized_payload.get("translated_text_vi")

                if not translated_title_vi and not translated_text_vi:
                    continue

                item["translated_title_vi"] = translated_title_vi
                item["translated_text_vi"] = translated_text_vi
                self.review_repository.update_review_translations(
                    review_id=item["id"],
                    translated_title_vi=translated_title_vi,
                    translated_text_vi=translated_text_vi,
                    translation_provider=normalized_payload.get("translation_provider"),
                    translation_target_language=normalized_payload.get("translation_target_language"),
                    translation_detected_source_language=normalized_payload.get(
                        "translation_detected_source_language"
                    ),
                )
                changed = True
            except Exception:
                self.db.rollback()
                continue

        if changed:
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()

        return items

    def _normalize_review_items(self, items: list[dict], *, rating_rules) -> list[dict]:
        normalized_items: list[dict] = []
        for item in items:
            normalized = dict(item)
            rating = normalized.get("rating")
            fallback_is_bad = bool(normalized.get("is_bad_review"))
            normalized["review_status"] = rating_rules.classify(
                rating,
                fallback_is_bad=fallback_is_bad,
            )
            normalized.pop("is_bad_review", None)
            normalized_items.append(normalized)
        return normalized_items

    @staticmethod
    def _has_translation(item: dict) -> bool:
        review_language = (item.get("review_language") or "").strip().lower()
        title = (item.get("review_title") or "").strip()
        text = (item.get("review_text") or "").strip()
        translated_title = (item.get("translated_title_vi") or "").strip()
        translated_text = (item.get("translated_text_vi") or "").strip()

        title_ok = not title or (
            translated_title
            and (review_language == "vi" or translated_title != title)
        )
        text_ok = not text or (
            translated_text
            and (review_language == "vi" or translated_text != text)
        )
        return title_ok and text_ok

    @staticmethod
    def _validate_review_filters(
        *,
        review_status: str | None,
        rating_min: float | None,
        rating_max: float | None,
        date_from: datetime | None,
        date_to: datetime | None,
        sort_by: str,
        sort_order: str,
    ) -> None:
        allowed_sort_by = {"reviewed_at", "rating", "created_at", "hotel_name", "reviewer_name"}
        allowed_sort_order = {"asc", "desc"}
        allowed_review_status = {"good", "average", "bad"}

        if rating_min is not None and rating_max is not None and rating_min > rating_max:
            raise ValueError("rating_min must be less than or equal to rating_max")
        if date_from is not None and date_to is not None and date_from > date_to:
            raise ValueError("date_from must be less than or equal to date_to")
        if sort_by not in allowed_sort_by:
            raise ValueError(
                "sort_by must be one of: reviewed_at, rating, created_at, hotel_name, reviewer_name"
            )
        if sort_order.lower() not in allowed_sort_order:
            raise ValueError("sort_order must be either 'asc' or 'desc'")
        if review_status is not None:
            normalized_statuses = [
                item.strip().lower()
                for item in review_status.split(",")
                if item.strip()
            ]
            if not normalized_statuses:
                raise ValueError("review_status must include at least one value")
            invalid_statuses = [
                item for item in normalized_statuses if item not in allowed_review_status
            ]
            if invalid_statuses:
                raise ValueError(
                    "review_status must contain only: good, average, bad"
                )
