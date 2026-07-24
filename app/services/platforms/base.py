from app.core.config import settings
from app.schemas.sync import ExternalReviewPayload


class BaseReviewMapper:
    platform_code: str = "base"

    def normalize(self, review: ExternalReviewPayload) -> dict:
        rating_scale = review.rating_scale or 10.0
        normalized_is_bad = bool(review.is_bad_review)

        if review.rating is not None:
            normalized_is_bad = normalized_is_bad or (
                review.rating < settings.bad_review_rating_threshold
            )

        return {
            "external_review_id": review.external_review_id,
            "review_url": review.review_url,
            "reviewer_name": review.reviewer_name,
            "reviewer_country_code": review.reviewer_country_code,
            "reviewer_profile": review.reviewer_profile,
            "rating": review.rating,
            "rating_scale": rating_scale,
            "review_title": review.review_title,
            "review_text": review.review_text,
            "review_language": review.review_language,
            "sentiment_label": review.sentiment_label,
            "is_bad_review": normalized_is_bad,
            "stay_date": review.stay_date,
            "reviewed_at": review.reviewed_at,
            "replied_at": review.replied_at,
            "source_created_at": review.source_created_at,
            "source_updated_at": review.source_updated_at,
            "raw_payload": review.raw_payload or review.model_dump(mode="json"),
            "normalized_payload": review.normalized_payload,
            "metadata": review.metadata,
        }
