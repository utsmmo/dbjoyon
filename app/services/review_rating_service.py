from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.admin_settings_repository import AdminSettingsRepository


REVIEW_RATING_AVERAGE_MIN_KEY = "review.rating_band_average_min"
REVIEW_RATING_GOOD_MIN_KEY = "review.rating_band_good_min"


@dataclass(frozen=True)
class ReviewRatingRules:
    average_min: float
    good_min: float

    def classify(self, rating: float | None, *, fallback_is_bad: bool = False) -> str:
        if rating is None:
            return "bad" if fallback_is_bad else "unrated"
        if rating >= self.good_min:
            return "good"
        if rating >= self.average_min:
            return "average"
        return "bad"

    def is_bad(self, rating: float | None, *, fallback_is_bad: bool = False) -> bool:
        return self.classify(rating, fallback_is_bad=fallback_is_bad) == "bad"


class ReviewRatingService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def load_rules(self) -> ReviewRatingRules:
        default_rules = self.default_rules()
        if self.db is None:
            return default_rules

        repository = AdminSettingsRepository(self.db)
        try:
            repository.ensure_settings_baseline()
            values = repository.get_setting_values(
                [
                    REVIEW_RATING_AVERAGE_MIN_KEY,
                    REVIEW_RATING_GOOD_MIN_KEY,
                ]
            )
        except SQLAlchemyError:
            return default_rules

        average_min = self._coerce_threshold(
            values.get(REVIEW_RATING_AVERAGE_MIN_KEY),
            default_rules.average_min,
        )
        good_min = self._coerce_threshold(
            values.get(REVIEW_RATING_GOOD_MIN_KEY),
            default_rules.good_min,
        )
        return self._normalize_rules(average_min=average_min, good_min=good_min)

    @staticmethod
    def default_rules() -> ReviewRatingRules:
        return ReviewRatingRules(
            average_min=float(settings.bad_review_rating_threshold),
            good_min=float(settings.good_review_rating_threshold),
        )

    @staticmethod
    def _coerce_threshold(value: str | None, fallback: float) -> float:
        if value is None or not str(value).strip():
            return fallback
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _normalize_rules(*, average_min: float, good_min: float) -> ReviewRatingRules:
        clamped_good_min = min(max(good_min, 0.0), 10.0)
        clamped_average_min = min(max(average_min, 0.0), clamped_good_min)
        return ReviewRatingRules(
            average_min=clamped_average_min,
            good_min=clamped_good_min,
        )
