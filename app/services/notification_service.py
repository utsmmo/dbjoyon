from sqlalchemy.orm import Session

from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    NotificationDeliveryUpsertRequest,
    NotificationDeliveryUpsertResponse,
    UnnotifiedBadReviewListResponse,
)


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.notification_repository = NotificationRepository(db)

    def list_unnotified_bad_reviews(
        self,
        *,
        channel_code: str,
        event_type: str,
        hotel_id: str | None,
        platform_code: str | None,
        limit: int,
        offset: int,
    ) -> UnnotifiedBadReviewListResponse:
        items, total = self.notification_repository.list_unnotified_bad_reviews(
            channel_code=channel_code,
            event_type=event_type,
            hotel_id=hotel_id,
            platform_code=platform_code,
            limit=limit,
            offset=offset,
        )
        return UnnotifiedBadReviewListResponse(
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

        delivery = self.notification_repository.upsert_delivery(
            review_id=payload.review_id,
            channel_code=payload.channel_code,
            event_type=payload.event_type,
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
