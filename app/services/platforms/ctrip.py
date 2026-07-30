from typing import Any

from app.services.platforms.base import BaseReviewMapper


def _to_float(value: Any) -> float | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        normalized = value.strip().replace(",", ".")
        if not normalized:
            return None
        try:
            return float(normalized)
        except ValueError:
            return None

    return None


class CtripReviewMapper(BaseReviewMapper):
    platform_code = "ctrip"

    def normalize(self, review):
        normalized = super().normalize(review)
        raw_payload = review.raw_payload or {}

        rating = normalized["rating"]
        if rating is None:
            rating = (
                _to_float(raw_payload.get("rating"))
                or _to_float(raw_payload.get("overall_score"))
                or _to_float(raw_payload.get("overallRating"))
                or _to_float(raw_payload.get("score"))
            )

        rating_scale = normalized["rating_scale"] or 10.0
        if review.rating_scale is None and rating is not None:
            rating_scale = (
                _to_float(raw_payload.get("rating_scale"))
                or _to_float(raw_payload.get("ratingScale"))
                or _to_float(raw_payload.get("score_scale"))
                or 10.0
            )

        normalized["rating"] = rating
        normalized["rating_scale"] = rating_scale

        if rating is not None:
            normalized["is_bad_review"] = bool(normalized["is_bad_review"]) or (
                rating < rating_scale * 0.7
            )

        return normalized
