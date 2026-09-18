from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.services.channex_webhook_service import ChannexWebhookError, ChannexWebhookService

router = APIRouter(prefix="/integrations/channex", tags=["channex-webhook"])
service = ChannexWebhookService()


def _build_webhook_url(request: Request) -> str:
    return str(request.url_for("receive_channex_webhook"))


@router.get("/health")
def get_channex_webhook_health(request: Request) -> dict:
    return service.get_health(_build_webhook_url(request))


@router.get("/webhook/info")
def get_channex_webhook_info(request: Request) -> dict:
    return service.get_webhook_info(_build_webhook_url(request))


@router.get("/channexapi/bookings/{booking_id}")
def get_channex_booking_detail(
    booking_id: str,
    relationships: str = "all",
    mode: str = "simple",
    authorization: str | None = Header(default=None),
) -> dict:
    try:
        return service.get_booking_detail_via_authorization(
            booking_id=booking_id,
            relationships=relationships,
            authorization=authorization or "",
            response_mode=mode.strip().lower(),
        )
    except ChannexWebhookError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"error": exc.code, "detail": exc.detail}) from exc


@router.post("/webhook", name="receive_channex_webhook")
def receive_channex_webhook(
    payload: dict,
    request: Request,
    x_channex_webhook_secret: str | None = Header(default=None),
) -> dict:
    try:
        _ = request
        return service.process_webhook(payload or {}, x_channex_webhook_secret or "")
    except ChannexWebhookError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"error": exc.code, "detail": exc.detail}) from exc
