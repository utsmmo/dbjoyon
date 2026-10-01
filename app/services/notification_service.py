from datetime import datetime, timedelta, timezone
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.admin_settings_repository import AdminSettingsRepository
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    LarkBadReviewSendItemResponse,
    LarkBadReviewSendRequest,
    LarkBadReviewSendResponse,
    NotificationDeliveryUpsertRequest,
    NotificationDeliveryUpsertResponse,
    UnnotifiedBadReviewListResponse,
)
from app.services.review_rating_service import ReviewRatingService


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.notification_repository = NotificationRepository(db)
        self.admin_settings_repository = AdminSettingsRepository(db)
        self.review_rating_service = ReviewRatingService(db)

    @staticmethod
    def _is_event_type_optional_channel(channel_code: str) -> bool:
        return channel_code.strip().lower() == "larknoibo"

    def list_unnotified_bad_reviews(
        self,
        *,
        review_label: str,
        channel_code: str,
        event_type: str,
        hotel_id: str | None,
        platform_code: str | None,
        recent_days: int,
        include_sent: bool,
        limit: int,
        offset: int,
    ) -> UnnotifiedBadReviewListResponse:
        reviewed_from = datetime.now(timezone.utc) - timedelta(days=recent_days)
        rating_rules = self.review_rating_service.load_rules()
        items, total = self.notification_repository.list_unnotified_bad_reviews(
            review_label=review_label,
            channel_code=channel_code,
            event_type=event_type,
            hotel_id=hotel_id,
            platform_code=platform_code,
            reviewed_from=reviewed_from,
            average_min=rating_rules.average_min,
            good_min=rating_rules.good_min,
            include_sent=include_sent,
            limit=limit,
            offset=offset,
        )
        items = self._normalize_review_items(items, rating_rules=rating_rules)
        return UnnotifiedBadReviewListResponse(
            review_label=review_label,
            channel_code=channel_code,
            event_type=event_type,
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    def upsert_delivery(
        self,
        payload: NotificationDeliveryUpsertRequest,
    ) -> NotificationDeliveryUpsertResponse:
        if payload.delivery_status not in {"pending", "sent", "failed", "skipped"}:
            raise ValueError(f"Unsupported delivery_status: {payload.delivery_status}")

        resolved_event_type = payload.event_type
        if not resolved_event_type and not self._is_event_type_optional_channel(payload.channel_code):
            raise ValueError("event_type is required for this channel_code")

        self.notification_repository.ensure_delivery_schema()
        delivery = self.notification_repository.upsert_delivery(
            review_id=payload.review_id,
            channel_code=payload.channel_code,
            event_type=resolved_event_type,
            delivery_status=payload.delivery_status,
            target_ref=payload.target_ref,
            external_message_id=payload.external_message_id,
            error_message=payload.error_message,
            request_payload=payload.request_payload,
            response_payload=payload.response_payload,
            metadata=payload.metadata,
        )
        self.db.commit()
        return NotificationDeliveryUpsertResponse(**delivery)

    def send_bad_reviews_to_lark(
        self,
        payload: LarkBadReviewSendRequest,
    ) -> LarkBadReviewSendResponse:
        review_label = payload.review_label
        event_type = payload.event_type or ("mixed_review" if review_label == "all" else f"{review_label}_review")
        self.notification_repository.ensure_delivery_schema()
        runtime_settings = self._resolve_lark_runtime_settings(payload.channel_code)
        webhook_url = (
            payload.webhook_url
            or runtime_settings["webhook_url"]
            or settings.lark_bad_review_webhook_url
        ).strip()
        if not webhook_url:
            raise ValueError("Missing Lark webhook URL. Set LARK_BAD_REVIEW_WEBHOOK_URL or pass webhook_url.")

        requested_review_ids = [item.strip() for item in payload.review_ids if item.strip()]
        if payload.review_id:
            requested_review_ids.append(payload.review_id.strip())
        requested_review_ids = list(dict.fromkeys(requested_review_ids))
        rating_rules = self.review_rating_service.load_rules()

        if requested_review_ids:
            reviews = self.notification_repository.get_bad_reviews_by_ids(
                review_ids=requested_review_ids,
                review_label=review_label,
                average_min=rating_rules.average_min,
                good_min=rating_rules.good_min,
            )
            if not reviews:
                raise ValueError("No matching review found for the provided review_id or review_ids.")
            reviews = self._normalize_review_items(reviews, rating_rules=rating_rules)
        else:
            queue = self.list_unnotified_bad_reviews(
                review_label=review_label,
                channel_code=payload.channel_code,
                event_type=event_type,
                hotel_id=payload.hotel_id,
                platform_code=payload.platform_code,
                recent_days=payload.recent_days,
                include_sent=payload.include_sent,
                limit=payload.limit,
                offset=0,
            )
            reviews = [item.model_dump(mode="json") for item in queue.items]

        items: list[LarkBadReviewSendItemResponse] = []

        for review in reviews:
            per_review_label = str(
                review.get("derived_review_label")
                or review.get("review_status")
            )
            per_event_type = str(
                review.get("derived_event_type")
                or ("mixed_review" if review_label == "all" else event_type)
            )
            request_payload = self._build_lark_message(review, review_label=per_review_label)
            try:
                response_payload = self._post_to_lark(
                    webhook_url=webhook_url,
                    request_payload=request_payload,
                    timeout_seconds=runtime_settings["timeout_seconds"],
                )
                external_message_id = self._extract_lark_message_id(response_payload)
                delivery = self.notification_repository.upsert_delivery(
                    review_id=review["id"],
                    channel_code=payload.channel_code,
                    event_type=per_event_type,
                    delivery_status="sent",
                    target_ref=payload.target_ref or webhook_url,
                    external_message_id=external_message_id,
                    error_message=None,
                    request_payload=request_payload,
                    response_payload=response_payload,
                    metadata={"provider": "lark"},
                )
                self.db.commit()
                items.append(
                    LarkBadReviewSendItemResponse(
                        review_id=review["id"],
                        hotel_name=review["hotel_name"],
                        platform_code=review["platform_code"],
                        delivery_status="sent",
                        external_message_id=external_message_id,
                        response_payload=response_payload,
                        delivery=NotificationDeliveryUpsertResponse(**delivery),
                    )
                )
            except Exception as exc:
                self.db.rollback()
                error_message = str(exc)
                failed_payload = {"ok": False, "error": error_message}
                delivery_response = None
                try:
                    delivery = self.notification_repository.upsert_delivery(
                        review_id=review["id"],
                        channel_code=payload.channel_code,
                        event_type=per_event_type,
                        delivery_status="failed",
                        target_ref=payload.target_ref or webhook_url,
                        external_message_id=None,
                        error_message=error_message,
                        request_payload=request_payload,
                        response_payload=failed_payload,
                        metadata={"provider": "lark"},
                    )
                    self.db.commit()
                    delivery_response = NotificationDeliveryUpsertResponse(**delivery)
                except Exception:
                    self.db.rollback()
                items.append(
                    LarkBadReviewSendItemResponse(
                        review_id=review["id"],
                        hotel_name=review["hotel_name"],
                        platform_code=review["platform_code"],
                        delivery_status="failed",
                        error_message=error_message,
                        response_payload=failed_payload,
                        delivery=delivery_response,
                    )
                )

        sent_count = sum(1 for item in items if item.delivery_status == "sent")
        failed_count = sum(1 for item in items if item.delivery_status == "failed")
        return LarkBadReviewSendResponse(
            channel_code=payload.channel_code,
            event_type=event_type,
            target_ref=payload.target_ref or webhook_url,
            requested_count=len(reviews),
            processed_count=len(items),
            sent_count=sent_count,
            failed_count=failed_count,
            items=items,
        )

    def _build_lark_message(self, review: dict[str, object], *, review_label: str) -> dict[str, object]:
        title = self._truncate_text(
            str(review.get("translated_title_vi") or review.get("review_title") or f"{review_label.title()} review alert").strip(),
            200,
        )
        body = self._truncate_text(
            str(review.get("translated_text_vi") or review.get("review_text") or "Khong co noi dung review").strip(),
            1200,
        )
        reviewer_name = str(review.get("reviewer_name") or "Anonymous").strip()
        reviewer_country_code = str(review.get("reviewer_country_code") or "Unknown").strip()
        rating = review.get("rating")
        rating_scale = review.get("rating_scale")
        rating_label = "-"
        if rating is not None and rating_scale is not None:
            rating_label = f"{rating}/{rating_scale}"
        reviewed_at = str(review.get("reviewed_at") or "")

        alert_title = "GOOD REVIEW ALERT" if review_label == "good" else "BAD REVIEW ALERT"
        content_lines = [
            alert_title,
            f"Hotel: {review['hotel_name']}",
            f"OTA: {review['platform_code']}",
            f"Score: {rating_label}",
            f"Guest: {reviewer_name} ({reviewer_country_code})",
            f"Reviewed at: {reviewed_at}",
            f"Title: {title}",
            f"Content: {body}",
            f"Review ID: {review['id']}",
        ]
        return {
            "msg_type": "text",
            "content": {
                "text": "\n".join(content_lines),
            },
        }

    def _truncate_text(self, value: str, limit: int) -> str:
        if len(value) <= limit:
            return value
        return f"{value[: max(limit - 3, 0)].rstrip()}..."

    def _post_to_lark(
        self,
        *,
        webhook_url: str,
        request_payload: dict[str, object],
        timeout_seconds: int,
    ) -> dict[str, object]:
        body = json.dumps(request_payload).encode("utf-8")
        request = Request(
            webhook_url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        timeout = max(timeout_seconds, 1)
        try:
            with urlopen(request, timeout=timeout) as response:
                raw_text = response.read().decode("utf-8", errors="replace")
                parsed = json.loads(raw_text) if raw_text else {}
                if not isinstance(parsed, dict):
                    parsed = {"raw_response": parsed}
                parsed.setdefault("http_status", response.status)
                self._raise_if_lark_error(parsed)
                return parsed
        except HTTPError as exc:
            raw_text = exc.read().decode("utf-8", errors="replace")
            detail = raw_text or exc.reason
            raise ValueError(f"Lark webhook HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise ValueError(f"Lark webhook connection failed: {exc.reason}") from exc

    def _raise_if_lark_error(self, response_payload: dict[str, object]) -> None:
        for key in ("code", "Code", "StatusCode", "statusCode"):
            value = response_payload.get(key)
            if value in (None, 0, "0", "", "success"):
                continue
            raise ValueError(f"Lark webhook rejected payload with {key}={value}")

    def _extract_lark_message_id(self, response_payload: dict[str, object]) -> str | None:
        direct_keys = ("message_id", "open_message_id", "msg_id", "request_id")
        for key in direct_keys:
            value = response_payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        data = response_payload.get("data")
        if isinstance(data, dict):
            for key in direct_keys:
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    def _resolve_lark_runtime_settings(self, channel_code: str) -> dict[str, object]:
        try:
            self.admin_settings_repository.ensure_settings_baseline()
            requested_keys = [f"notification.{channel_code}_webhook_url", "notification.lark_timeout_seconds"]
            if channel_code == "lark":
                requested_keys.insert(0, "notification.lark_bad_review_webhook_url")
            values = self.admin_settings_repository.get_setting_values(requested_keys)
        except Exception:
            values = {}

        webhook_url = str(
            values.get(f"notification.{channel_code}_webhook_url")
            or values.get("notification.lark_bad_review_webhook_url")
            or ""
        ).strip()
        timeout_raw = values.get("notification.lark_timeout_seconds")
        try:
            timeout_seconds = int(str(timeout_raw or settings.lark_notification_timeout_seconds).strip())
        except (TypeError, ValueError):
            timeout_seconds = settings.lark_notification_timeout_seconds

        return {
            "webhook_url": webhook_url,
            "timeout_seconds": max(timeout_seconds, 1),
        }

    def _normalize_review_items(self, items: list[dict], *, rating_rules) -> list[dict]:
        normalized_items: list[dict] = []
        for item in items:
            normalized = dict(item)
            normalized["review_status"] = rating_rules.classify(
                normalized.get("rating"),
                fallback_is_bad=bool(normalized.get("is_bad_review")),
            )
            normalized.pop("is_bad_review", None)
            normalized_items.append(normalized)
        return normalized_items
