from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.platform_repository import PlatformRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewListResponse, ReviewStatsListResponse
from app.services.translation_service import TranslationService


class ReviewQueryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.review_repository = ReviewRepository(db)
        self.platform_repository = PlatformRepository(db)
        self.translation_service = TranslationService()

    def list_reviews(
        self,
        *,
        hotel_id: str | None,
        platform_code: str | None,
        is_bad_review: bool | None,
        limit: int,
        offset: int,
    ) -> ReviewListResponse:
        items, total = self.review_repository.list_reviews(
            hotel_id=hotel_id,
            platform_code=platform_code,
            is_bad_review=is_bad_review,
            limit=limit,
            offset=offset,
        )
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
                corrected_bad_flag = self._compute_bad_review(item)
                if item.get("is_bad_review") != corrected_bad_flag:
                    item["is_bad_review"] = corrected_bad_flag
                    self.review_repository.update_review_bad_flag(
                        review_id=item["id"],
                        is_bad_review=corrected_bad_flag,
                    )
                    changed = True

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

    @staticmethod
    def _compute_bad_review(item: dict) -> bool:
        rating = item.get("rating")
        if rating is None:
            return bool(item.get("is_bad_review"))
        return float(rating) < settings.bad_review_rating_threshold

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
