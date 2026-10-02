from app.schemas.sync import ExternalReviewPayload


class BaseReviewMapper:
    platform_code: str = "base"

    @staticmethod
    def _coerce_text(value: object) -> str:
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            for key in ("text", "value", "content", "label", "title", "comment"):
                nested = value.get(key)
                if isinstance(nested, str) and nested.strip():
                    return nested.strip()
        return ""

    def _extract_pros_cons(self, review: ExternalReviewPayload) -> tuple[str, str]:
        candidate_payloads = [review.normalized_payload or {}, review.raw_payload or {}]
        positive_keys = ("pros", "positive", "liked", "review_pos", "advantages")
        negative_keys = ("cons", "negative", "disliked", "review_neg", "disadvantages")

        pros = ""
        cons = ""

        for payload in candidate_payloads:
            if not isinstance(payload, dict):
                continue

            if not pros:
                for key in positive_keys:
                    pros = self._coerce_text(payload.get(key))
                    if pros:
                        break

            if not cons:
                for key in negative_keys:
                    cons = self._coerce_text(payload.get(key))
                    if cons:
                        break

            if pros and cons:
                break

        return pros, cons

    @staticmethod
    def _compose_review_text(review_text: str | None, pros: str, cons: str) -> str | None:
        base_text = (review_text or "").strip()
        if not pros and not cons:
            return base_text or None

        parts: list[str] = []
        if base_text and base_text not in {pros, cons}:
            parts.append(base_text)
        if pros:
            parts.append(f"Uu diem:\n{pros}")
        if cons:
            parts.append(f"Nhuoc diem:\n{cons}")

        return "\n\n".join(parts).strip() or None

    def normalize(self, review: ExternalReviewPayload) -> dict:
        rating_scale = review.rating_scale or 10.0
        normalized_is_bad = bool(review.is_bad_review)
        normalized_payload = dict(review.normalized_payload or {})
        pros, cons = self._extract_pros_cons(review)
        review_text = self._compose_review_text(review.review_text, pros, cons)

        if pros:
            normalized_payload["pros"] = pros
        if cons:
            normalized_payload["cons"] = cons

        return {
            "external_review_id": review.external_review_id,
            "review_url": review.review_url,
            "reviewer_name": review.reviewer_name,
            "reviewer_country_code": review.reviewer_country_code,
            "reviewer_profile": review.reviewer_profile,
            "rating": review.rating,
            "rating_scale": rating_scale,
            "review_title": review.review_title,
            "review_text": review_text,
            "review_language": review.review_language,
            "sentiment_label": review.sentiment_label,
            "is_bad_review": normalized_is_bad,
            "stay_date": review.stay_date,
            "reviewed_at": review.reviewed_at,
            "replied_at": review.replied_at,
            "source_created_at": review.source_created_at,
            "source_updated_at": review.source_updated_at,
            "raw_payload": review.raw_payload or review.model_dump(mode="json"),
            "normalized_payload": normalized_payload,
            "metadata": review.metadata,
        }
