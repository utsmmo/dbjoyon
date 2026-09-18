from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request


@dataclass
class ChannexWebhookError(Exception):
    code: str
    status_code: int
    detail: Any | None = None

    def __str__(self) -> str:
        return self.code


class ChannexWebhookService:
    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parents[2]
        self.idempotency_store_file = Path(
            os.getenv("CHANNEX_IDEMPOTENCY_STORE_FILE", "./data/channex-processed-events.json")
        ).resolve()
        self.raw_log_dir = Path(os.getenv("CHANNEX_RAW_LOG_DIR", "./data/channex-raw-events")).resolve()
        self.channex_env_file = self._resolve_project_path(os.getenv("CHANNEX_ENV_FILE") or "./env.channex")

        self.idempotency_store_file.parent.mkdir(parents=True, exist_ok=True)
        self.raw_log_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_project_path(self, raw_path: str) -> Path:
        candidate = Path(raw_path)
        if candidate.is_absolute():
            return candidate.resolve()
        return (self.project_root / candidate).resolve()

    def get_health(self, webhook_url: str) -> dict[str, Any]:
        return {
            "ok": True,
            "service": "channex-webhook-bridge",
            "webhook_url": webhook_url,
        }

    def get_webhook_info(self, webhook_url: str) -> dict[str, Any]:
        runtime = self._get_runtime_config()
        return {
            "ok": True,
            "webhook_url": webhook_url,
            "method": "POST",
            "recommended_webhook_config": {
                "callback_url": webhook_url,
                "event_mask": runtime["channex_event_mask"],
                "send_data": runtime["channex_send_data"],
                "is_global": runtime["channex_is_global"],
                "property_id": runtime["channex_property_id"],
                "headers": {
                    "X-Channex-Webhook-Secret": "<your-configured-secret>"
                    if runtime["channex_webhook_secret"]
                    else "<missing-secret-in-settings-or-env>",
                },
            },
            "required_header": {
                "name": "X-Channex-Webhook-Secret",
                "value": "<your-configured-secret>"
                if runtime["channex_webhook_secret"]
                else "<missing-secret-in-settings-or-env>",
            },
            "sample_payload": {
                "event": "booking",
                "payload": {
                    "booking_id": "e10de9d1-3e2c-431c-b88c-ffca9ed5db5d",
                    "property_id": "90958ec0-9713-1196-873e-4add0d834670",
                    "revision_id": "80b3b60c-5e24-35c5-ad1b-da67cd704093",
                },
                "property_id": "90958ec0-9713-1396-873e-4add0d834670",
                "user_id": None,
                "timestamp": "2021-12-24T00:00:00.0000Z",
            },
            "note": "Channex webhook is only a trigger. The receiver fetches booking detail by booking_id before forwarding.",
            "important_notes": [
                "send_data must stay enabled for booking events so booking_id and revision_id are included in the webhook payload.",
                "Webhook events can arrive out of order. Use the payload as a trigger, then pull the latest booking detail from Channex.",
                "Use a strong shared secret in X-Channex-Webhook-Secret and rotate it per environment when needed.",
            ],
        }

    def process_webhook(self, payload: dict[str, Any], provided_secret: str) -> dict[str, Any]:
        received_at = self._now_iso()
        runtime = self._get_runtime_config()

        if not runtime["channex_webhook_secret"] or provided_secret != runtime["channex_webhook_secret"]:
            raise ChannexWebhookError(code="invalid_secret", status_code=401)

        event_name = str(payload.get("event") or payload.get("type") or "").strip()
        identifiers = self.extract_webhook_identifiers(payload)
        booking_id = identifiers["booking_id"]
        revision_id = identifiers["revision_id"]
        property_id = identifiers["property_id"]

        if not event_name:
            raise ChannexWebhookError(
                code="invalid_payload",
                status_code=400,
                detail={
                    "required_fields": ["event", "booking_id"],
                    "received_shape": self.summarize_webhook_payload(payload),
                },
            )

        if not booking_id:
            self.write_raw_webhook_log(
                {
                    "received_at": received_at,
                    "event_name": event_name,
                    "booking_id": None,
                    "revision_id": revision_id,
                    "property_id": property_id,
                    "payload": payload,
                    "status": "test_or_incomplete_payload_acknowledged",
                }
            )
            return {
                "success": True,
                "acknowledged": True,
                "mode": "test_or_incomplete_payload",
                "event": event_name,
                "message": "Webhook received, but no booking_id was provided. This is expected for some Channex test messages.",
            }

        idempotency_key = self.build_idempotency_key(
            event_name=event_name,
            booking_id=booking_id,
            revision_id=revision_id,
            timestamp=str(payload.get("timestamp") or ""),
        )

        duplicate = self.has_processed_event(idempotency_key)
        self.write_raw_webhook_log(
            {
                "received_at": received_at,
                "event_name": event_name,
                "booking_id": booking_id,
                "revision_id": revision_id,
                "property_id": property_id,
                "idempotency_key": idempotency_key,
                "payload": payload,
                "status": "duplicate_ignored" if duplicate else "received",
            }
        )

        if duplicate:
            return {
                "success": True,
                "duplicate": True,
                "booking_id": booking_id,
            }

        if runtime["channex_realtime_passthrough_mode"]:
            passthrough = self.build_passthrough_payload(
                webhook_payload=payload,
                property_id=property_id,
                received_at=received_at,
                idempotency_key=idempotency_key,
            )
            self.forward_to_n8n(passthrough, runtime=runtime)
            self.mark_processed(idempotency_key, passthrough)
            return {
                "success": True,
                "booking_id": passthrough["booking_id"],
                "channel": passthrough["destination"]["channel"],
                "mode": "passthrough",
            }

        booking = self.fetch_booking_by_id(booking_id, runtime=runtime)
        normalized = self.normalize_booking_event(
            webhook_payload=payload,
            booking=booking,
            property_id=property_id,
            received_at=received_at,
            idempotency_key=idempotency_key,
            runtime=runtime,
        )
        self.forward_to_n8n(normalized, runtime=runtime)
        self.mark_processed(idempotency_key, normalized)

        return {
            "success": True,
            "booking_id": normalized["booking_id"],
            "channel": normalized["destination"]["channel"],
        }

    def get_booking_detail_via_authorization(
        self,
        *,
        booking_id: str,
        relationships: str,
        authorization: str,
        response_mode: str,
    ) -> dict[str, Any]:
        if not booking_id.strip():
            raise ChannexWebhookError(code="missing_booking_id", status_code=400)

        runtime = self._get_runtime_config()
        resolved_authorization = authorization.strip()

        if not resolved_authorization:
            raise ChannexWebhookError(
                code="missing_authorization_header",
                status_code=400,
                detail="Pass Channex Bearer token in the Authorization header.",
            )

        if not resolved_authorization.lower().startswith("bearer "):
            resolved_authorization = f"Bearer {resolved_authorization}"

        booking = self.fetch_booking_by_authorization(
            booking_id=booking_id.strip(),
            relationships=relationships.strip() or "all",
            authorization=resolved_authorization,
            runtime=runtime,
        )
        hotel = self.resolve_property_metadata(booking=booking, runtime=runtime)
        summary = self.build_booking_summary(booking=booking, hotel=hotel)

        if response_mode == "full":
            return {
                "success": True,
                "booking_id": booking_id.strip(),
                "relationships": relationships.strip() or "all",
                "hotel": hotel,
                "summary": summary,
                "data": booking,
            }

        return {
            "success": True,
            "booking_id": booking_id.strip(),
            **summary,
        }

    def build_booking_summary(self, *, booking: dict[str, Any], hotel: dict[str, Any]) -> dict[str, Any]:
        booking_data = booking.get("data") if isinstance(booking.get("data"), dict) else {}
        attributes = booking_data.get("attributes") if isinstance(booking_data.get("attributes"), dict) else {}
        customer = attributes.get("customer") if isinstance(attributes.get("customer"), dict) else {}
        meta = attributes.get("meta") if isinstance(attributes.get("meta"), dict) else {}
        guest_message = self.extract_guest_message(attributes)
        ota_name = self._pick_string(attributes.get("ota_name"))
        source_platform = self.normalize_source_platform(ota_name)
        ota_display_name = self.resolve_ota_display_name(source_platform, ota_name)

        first_name = self._pick_string(customer.get("name"))
        last_name = self._pick_string(customer.get("surname"))
        customer_phone = self._pick_string(customer.get("phone"))
        customer_country = self._pick_string(customer.get("country"))
        phone_normalized = self.normalize_phone(customer_phone)
        phone_quality = self.resolve_customer_phone_quality(
            customer_phone=customer_phone,
            source_platform=source_platform,
        )
        country_routing = self.resolve_country_routing(
            customer_country=customer_country,
            phone_normalized=phone_normalized,
        )
        target_channel = country_routing["target_channel"]
        chat_account = self.resolve_hotel_chat_account(hotel=hotel, target_channel=target_channel)

        return {
            "booking_id": self._pick_string(attributes.get("booking_id"), booking_data.get("id")),
            "property_id": hotel.get("property_id"),
            "hotel_id": self._pick_string(meta.get("hotel_id")),
            "hotel_code": hotel.get("hotel_code"),
            "hotel_name": hotel.get("hotel_name"),
            "ota_name": ota_display_name,
            "reservation_id": self._pick_string(attributes.get("unique_id")),
            "ota_reservation_id": self._pick_string(attributes.get("ota_reservation_code")),
            "ota_reservation_code": self._pick_string(attributes.get("ota_reservation_code")),
            "channel_id": self._pick_string(attributes.get("channel_id")),
            "revision_id": self._pick_string(attributes.get("revision_id")),
            "status": self._pick_string(attributes.get("status")),
            "customer_name": " ".join(part for part in [first_name, last_name] if part) or None,
            "customer_phone": phone_normalized or customer_phone,
            "customer_phone_is_usable": phone_quality["is_usable"],
            "customer_phone_quality": phone_quality,
            "customer_email": self._pick_string(customer.get("mail")),
            "customer_country": customer_country,
            "country_routing": country_routing,
            "guest_message": guest_message,
            "arrival_date": self._pick_string(attributes.get("arrival_date")),
            "departure_date": self._pick_string(attributes.get("departure_date")),
            "amount": attributes.get("amount"),
            "currency": self._pick_string(attributes.get("currency")),
            "target_channel": target_channel,
            "route_key": f"{hotel.get('hotel_code') or 'UNKNOWN'}:{target_channel}",
            "chat_account": chat_account,
            "chat_routing": {
                "target_channel": target_channel,
                "route_key": f"{hotel.get('hotel_code') or 'UNKNOWN'}:{target_channel}",
                "hotel_code": hotel.get("hotel_code"),
                "hotel_name": hotel.get("hotel_name"),
                "account": chat_account,
                "country": country_routing,
            },
        }

    def extract_guest_message(self, attributes: dict[str, Any]) -> str | None:
        notes = self._pick_string(attributes.get("notes"))
        if not notes:
            return None

        ota_name = (self._pick_string(attributes.get("ota_name")) or "").lower()
        normalized_notes = notes.replace("\r\n", "\n").replace("\r", "\n")

        if "booking" in ota_name:
            lines = [line.strip() for line in normalized_notes.split("\n") if line.strip()]
            kept: list[str] = []
            stop_prefixes = (
                "meal plan:",
                "smoking preference:",
                "payment collect:",
                "ota commission:",
                "chính sách",
                "chinh sach",
                "bữa sáng",
                "bua sang",
                "bữa tối",
                "bua toi",
            )
            for line in lines:
                if line.lower().startswith(stop_prefixes):
                    break
                kept.append(line)
            message = "\n".join(kept).strip()
            return message or None

        if "ctrip" in ota_name or "trip" in ota_name:
            parts = [part.strip() for part in normalized_notes.split(";") if part.strip()]
            ignored_prefixes = (
                "diamond member",
                "basic deal",
                "mobile rate",
                "for contacting the guest please dial",
                "please contact guest by system generated mail",
                "preferred language",
                "traffic boost fee",
                "this booking was made through trip.com",
                "contact guest by",
                "contact trip.com via",
                "+44-",
                "+84-",
                "meal plan for room",
            )
            kept = [part for part in parts if not part.lower().startswith(ignored_prefixes)]
            message = "; ".join(kept).strip()
            return message or None

        stripped = normalized_notes.strip()
        return stripped or None

    def build_passthrough_payload(
        self,
        *,
        webhook_payload: dict[str, Any],
        property_id: str | None,
        received_at: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        identifiers = self.extract_webhook_identifiers(webhook_payload)
        source_domain = self.derive_source_domain_from_webhook(webhook_payload)
        destination = self.resolve_destination(source_domain, booking_channel_map=self._get_runtime_config()["booking_channel_map"])
        hotel = self.resolve_property_metadata_from_id(property_id or identifiers["property_id"], runtime=self._get_runtime_config())

        return {
            "source": "channex",
            "mode": "passthrough",
            "event": str(webhook_payload.get("event") or webhook_payload.get("type") or ""),
            "timestamp": self._pick_string(webhook_payload.get("timestamp")) or received_at,
            "received_at": received_at,
            "idempotency_key": idempotency_key,
            "property_id": property_id or identifiers["property_id"],
            "hotel": hotel,
            "booking_id": identifiers["booking_id"],
            "revision_id": identifiers["revision_id"],
            "source_domain": source_domain,
            "destination": destination,
            "guest": {
                "full_name": None,
                "email": None,
                "phone_raw": None,
                "phone_normalized": None,
            },
            "raw_webhook": webhook_payload,
            "next_step": {
                "action": "fetch_booking_detail_in_n8n",
                "endpoint": "/api/v1/integrations/channex/channexapi/bookings/{booking_id}?relationships=all",
                "authorization_header_required": True,
            },
        }

    def extract_webhook_identifiers(self, payload: dict[str, Any]) -> dict[str, str | None]:
        nested_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
        nested_data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        return {
            "booking_id": self._pick_string(
                nested_payload.get("booking_id"),
                nested_data.get("booking_id"),
                payload.get("booking_id"),
            ),
            "revision_id": self._pick_string(
                nested_payload.get("revision_id"),
                nested_data.get("revision_id"),
                payload.get("revision_id"),
            ),
            "property_id": self._pick_string(
                nested_payload.get("property_id"),
                nested_data.get("property_id"),
                payload.get("property_id"),
            ),
        }

    def summarize_webhook_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        nested_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
        nested_data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        return {
            "top_level_keys": list(payload.keys()),
            "payload_keys": list(nested_payload.keys()),
            "data_keys": list(nested_data.keys()),
        }

    def fetch_booking_by_id(self, booking_id: str, *, runtime: dict[str, Any]) -> dict[str, Any]:
        if not runtime["channex_api_base_url"] or not runtime["channex_api_key"]:
            raise ChannexWebhookError(code="missing_channex_api_config", status_code=500)

        request = urllib_request.Request(
            f"{runtime['channex_api_base_url']}/bookings/{booking_id}",
            headers={
                "user-api-key": runtime["channex_api_key"],
                "Content-Type": "application/json",
            },
            method="GET",
        )

        try:
            with urllib_request.urlopen(request, timeout=runtime["request_timeout_seconds"]) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except urllib_error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise ChannexWebhookError(
                code="channex_api_error",
                status_code=500,
                detail={"status_code": exc.code, "body": body},
            ) from exc
        except urllib_error.URLError as exc:
            raise ChannexWebhookError(code="channex_api_unreachable", status_code=500, detail=str(exc)) from exc

    def fetch_booking_by_authorization(
        self,
        booking_id: str,
        *,
        relationships: str,
        authorization: str,
        runtime: dict[str, Any],
    ) -> dict[str, Any]:
        if not runtime["channex_app_api_base_url"]:
            raise ChannexWebhookError(code="missing_channex_app_api_base_url", status_code=500)

        try:
            return self._fetch_booking_with_authorization(
                booking_id=booking_id,
                relationships=relationships,
                authorization=authorization,
                runtime=runtime,
            )
        except ChannexWebhookError as exc:
            is_env_token = authorization == self._format_bearer_token(runtime["channex_bearer_token"])
            can_refresh = (
                bool(runtime["channex_refresh_token"])
                and isinstance(exc.detail, dict)
                and exc.detail.get("status_code") == 401
            )
            if not is_env_token or not can_refresh:
                raise

            refreshed = self.refresh_channex_session(runtime=runtime)
            runtime["channex_bearer_token"] = refreshed["auth_token"]
            runtime["channex_refresh_token"] = refreshed["refresh_token"]
            return self._fetch_booking_with_authorization(
                booking_id=booking_id,
                relationships=relationships,
                authorization=self._format_bearer_token(refreshed["auth_token"]),
                runtime=runtime,
            )

    def _fetch_booking_with_authorization(
        self,
        *,
        booking_id: str,
        relationships: str,
        authorization: str,
        runtime: dict[str, Any],
    ) -> dict[str, Any]:
        request = urllib_request.Request(
            f"{runtime['channex_app_api_base_url']}/bookings/{booking_id}?relationships={relationships}",
            headers={
                "Authorization": authorization,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="GET",
        )

        try:
            with urllib_request.urlopen(request, timeout=runtime["request_timeout_seconds"]) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except urllib_error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise ChannexWebhookError(
                code="channex_app_api_error",
                status_code=500,
                detail={"status_code": exc.code, "body": body},
            ) from exc
        except urllib_error.URLError as exc:
            raise ChannexWebhookError(code="channex_app_api_unreachable", status_code=500, detail=str(exc)) from exc

    def refresh_channex_session(self, *, runtime: dict[str, Any]) -> dict[str, str]:
        if not runtime["channex_refresh_token"]:
            raise ChannexWebhookError(code="missing_channex_refresh_token", status_code=500)

        request = urllib_request.Request(
            f"{runtime['channex_app_api_base_url']}/refresh",
            headers={
                "Authorization": self._format_bearer_token(runtime["channex_refresh_token"]),
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib_request.urlopen(request, timeout=runtime["request_timeout_seconds"]) as response:
                body = response.read().decode("utf-8")
                parsed = json.loads(body)
        except urllib_error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise ChannexWebhookError(
                code="channex_refresh_error",
                status_code=500,
                detail={"status_code": exc.code, "body": body},
            ) from exc
        except urllib_error.URLError as exc:
            raise ChannexWebhookError(code="channex_refresh_unreachable", status_code=500, detail=str(exc)) from exc

        attributes = (
            parsed.get("data", {}).get("attributes", {})
            if isinstance(parsed.get("data"), dict)
            else {}
        )
        auth_token = self._pick_string(attributes.get("token"))
        refresh_token = self._pick_string(attributes.get("refresh_token"))
        if not auth_token or not refresh_token:
            raise ChannexWebhookError(code="invalid_channex_refresh_response", status_code=500)

        self.write_channex_token_state(auth_token=auth_token, refresh_token=refresh_token, runtime=runtime)
        return {"auth_token": auth_token, "refresh_token": refresh_token}

    def normalize_booking_event(
        self,
        *,
        webhook_payload: dict[str, Any],
        booking: dict[str, Any],
        property_id: str | None,
        received_at: str,
        idempotency_key: str,
        runtime: dict[str, Any],
    ) -> dict[str, Any]:
        booking_data = booking.get("data") if isinstance(booking.get("data"), dict) else booking
        attributes = booking_data.get("attributes") if isinstance(booking_data.get("attributes"), dict) else booking_data
        customer = attributes.get("customer") if isinstance(attributes.get("customer"), dict) else {}
        source_domain = self.derive_domain(attributes)
        destination = self.resolve_destination(source_domain, booking_channel_map=runtime["booking_channel_map"])
        hotel = self.resolve_property_metadata(booking=booking, runtime=runtime)
        phone_raw = self._pick_string(customer.get("phone"))

        return {
            "source": "channex",
            "event": str(webhook_payload.get("event") or webhook_payload.get("type") or ""),
            "timestamp": self._pick_string(webhook_payload.get("timestamp")) or received_at,
            "received_at": received_at,
            "idempotency_key": idempotency_key,
            "property_id": property_id,
            "hotel": hotel,
            "booking_id": self._pick_string(booking_data.get("id")) or self.extract_webhook_identifiers(webhook_payload)["booking_id"],
            "revision_id": self._pick_string(attributes.get("revision_id"))
            or self.extract_webhook_identifiers(webhook_payload)["revision_id"],
            "status": self._pick_string(attributes.get("status")),
            "ota_name": self._pick_string(attributes.get("ota_name")),
            "source_domain": source_domain,
            "destination": destination,
            "guest": {
                "first_name": self._pick_string(customer.get("name")),
                "last_name": self._pick_string(customer.get("surname")),
                "full_name": " ".join(
                    part
                    for part in [self._pick_string(customer.get("name")), self._pick_string(customer.get("surname"))]
                    if part
                )
                or None,
                "email": self._pick_string(customer.get("mail")),
                "phone_raw": phone_raw,
                "phone_normalized": self.normalize_phone(phone_raw),
                "country": self._pick_string(customer.get("country")),
                "city": self._pick_string(customer.get("city")),
            },
            "stay": {
                "arrival_date": self._pick_string(attributes.get("arrival_date")),
                "departure_date": self._pick_string(attributes.get("departure_date")),
                "arrival_hour": self._pick_string(attributes.get("arrival_hour")),
                "currency": self._pick_string(attributes.get("currency")),
                "amount": attributes.get("amount"),
                "notes": self._pick_string(attributes.get("notes")),
            },
            "raw_booking": booking,
            "raw_webhook": webhook_payload,
        }

    def derive_domain(self, attributes: dict[str, Any]) -> str:
        candidates = [
            self._pick_string(attributes.get("ota_name")),
            self._pick_string(attributes.get("referer")),
            self._pick_string(attributes.get("source")),
            self._pick_string(attributes.get("channel")),
        ]
        return str(next((item for item in candidates if item), "default")).strip().lower()

    def derive_source_domain_from_webhook(self, payload: dict[str, Any]) -> str:
        nested_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
        nested_data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        candidates = [
            self._pick_string(payload.get("domain")),
            self._pick_string(payload.get("source")),
            self._pick_string(payload.get("channel")),
            self._pick_string(nested_payload.get("domain")),
            self._pick_string(nested_payload.get("source")),
            self._pick_string(nested_payload.get("channel")),
            self._pick_string(nested_data.get("domain")),
            self._pick_string(nested_data.get("source")),
            self._pick_string(nested_data.get("channel")),
            self._pick_string(payload.get("event")),
        ]
        return str(next((item for item in candidates if item), "default")).strip().lower()

    def resolve_destination(self, source_domain: str, *, booking_channel_map: dict[str, Any]) -> dict[str, Any]:
        if isinstance(booking_channel_map.get(source_domain), dict):
            return booking_channel_map[source_domain]
        if isinstance(booking_channel_map.get("default"), dict):
            return booking_channel_map["default"]
        return {
            "channel": "manual_review",
            "reason": f"No mapping for source_domain={source_domain}",
        }

    def resolve_property_metadata(self, *, booking: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
        booking_data = booking.get("data") if isinstance(booking.get("data"), dict) else booking
        attributes = booking_data.get("attributes") if isinstance(booking_data.get("attributes"), dict) else {}
        relationships = booking_data.get("relationships") if isinstance(booking_data.get("relationships"), dict) else {}
        property_id = self._pick_string(
            attributes.get("property_id"),
            booking_data.get("property_id"),
        )
        relationship_properties = relationships.get("properties", {}).get("data")
        property_title = None
        if isinstance(relationship_properties, list) and relationship_properties:
            first_property = relationship_properties[0]
            if isinstance(first_property, dict):
                property_title = self._pick_string(
                    first_property.get("attributes", {}).get("title") if isinstance(first_property.get("attributes"), dict) else None
                )
        return self.resolve_property_metadata_from_id(property_id, runtime=runtime, fallback_name=property_title)

    def resolve_property_metadata_from_id(
        self,
        property_id: str | None,
        *,
        runtime: dict[str, Any],
        fallback_name: str | None = None,
    ) -> dict[str, Any]:
        property_map = runtime["channex_property_map"]
        matched = property_map.get(property_id or "")
        if isinstance(matched, dict):
            return {
                "property_id": property_id,
                "hotel_code": self._pick_string(matched.get("hotel_code")),
                "hotel_name": self._pick_string(matched.get("hotel_name"), fallback_name),
                "chat_accounts": matched.get("chat_accounts") if isinstance(matched.get("chat_accounts"), dict) else {},
            }
        return {
            "property_id": property_id,
            "hotel_code": None,
            "hotel_name": fallback_name,
            "chat_accounts": {},
        }

    def resolve_target_chat_channel(self, *, customer_country: str | None, phone_normalized: str | None) -> str:
        return self.resolve_country_routing(
            customer_country=customer_country,
            phone_normalized=phone_normalized,
        )["target_channel"]

    def resolve_country_routing(self, *, customer_country: str | None, phone_normalized: str | None) -> dict[str, Any]:
        country = (customer_country or "").strip().upper()
        is_vietnam = country in {"VN", "VNM", "VIETNAM", "VIET NAM"}
        if is_vietnam:
            return {
                "country_code": customer_country,
                "is_vietnam": True,
                "target_channel": "zalo",
                "message_language": "vi",
                "reason": "customer_country_is_vietnam",
            }
        message_language = self.resolve_message_language(country)
        return {
            "country_code": customer_country,
            "is_vietnam": False,
            "target_channel": "whatsapp",
            "message_language": message_language,
            "reason": "non_vietnam_customer",
        }

    def resolve_message_language(self, country: str) -> str:
        language_map = {
            "CN": "zh",
            "CHN": "zh",
            "CHINA": "zh",
            "TW": "zh",
            "TWN": "zh",
            "HK": "zh",
            "HKG": "zh",
            "KR": "ko",
            "KOR": "ko",
            "KOREA": "ko",
            "JP": "ja",
            "JPN": "ja",
            "JAPAN": "ja",
            "TH": "th",
            "THA": "th",
            "THAILAND": "th",
            "RU": "ru",
            "RUS": "ru",
            "RUSSIA": "ru",
        }
        return language_map.get(country, "en")

    def normalize_source_platform(self, ota_name: str | None) -> str:
        value = (ota_name or "").strip().lower()
        if "agoda" in value:
            return "agoda"
        if "booking" in value:
            return "booking"
        if "ctrip" in value or "trip" in value:
            return "trip"
        if "expedia" in value:
            return "expedia"
        if "airbnb" in value:
            return "airbnb"
        return value or "unknown"

    def resolve_ota_display_name(self, source_platform: str, ota_name: str | None) -> str:
        display_map = {
            "agoda": "Agoda",
            "booking": "Booking",
            "trip": "Trip",
            "expedia": "Expedia",
            "airbnb": "Airbnb",
        }
        return display_map.get(source_platform, self._pick_string(ota_name) or "Unknown")

    def resolve_customer_phone_quality(self, *, customer_phone: str | None, source_platform: str) -> dict[str, Any]:
        has_phone = bool((customer_phone or "").strip())
        trusted_platforms = {"agoda", "booking"}
        if not has_phone:
            return {
                "is_usable": False,
                "reason": "missing_phone",
                "trusted_platforms": sorted(trusted_platforms),
            }
        if source_platform in trusted_platforms:
            return {
                "is_usable": True,
                "reason": "trusted_ota_phone",
                "trusted_platforms": sorted(trusted_platforms),
            }
        return {
            "is_usable": False,
            "reason": "untrusted_ota_proxy_phone",
            "trusted_platforms": sorted(trusted_platforms),
        }

    def resolve_hotel_chat_account(self, *, hotel: dict[str, Any], target_channel: str) -> dict[str, Any] | None:
        chat_accounts = hotel.get("chat_accounts")
        if not isinstance(chat_accounts, dict):
            return None
        account = chat_accounts.get(target_channel)
        if isinstance(account, dict):
            return account
        return None

    def normalize_phone(self, value: str | None) -> str | None:
        if not value:
            return None
        compact = "".join(char for char in value if char.isdigit() or char == "+")
        if not compact:
            return None
        if compact.startswith("+"):
            return compact
        if compact.startswith("00"):
            return f"+{compact[2:]}"
        if compact.startswith("0"):
            return f"+84{compact[1:]}"
        return f"+{compact}"

    def forward_to_n8n(self, payload: dict[str, Any], *, runtime: dict[str, Any]) -> None:
        if not runtime["n8n_forward_webhook_url"]:
            raise ChannexWebhookError(code="missing_n8n_forward_webhook_url", status_code=500)

        headers = {
            "Content-Type": "application/json",
        }
        if runtime["n8n_forward_webhook_token"]:
            headers["X-Bridge-Token"] = runtime["n8n_forward_webhook_token"]

        request = urllib_request.Request(
            runtime["n8n_forward_webhook_url"],
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib_request.urlopen(request, timeout=runtime["request_timeout_seconds"]):
                return
        except urllib_error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise ChannexWebhookError(
                code="n8n_webhook_error",
                status_code=500,
                detail={"status_code": exc.code, "body": body},
            ) from exc
        except urllib_error.URLError as exc:
            raise ChannexWebhookError(code="n8n_webhook_unreachable", status_code=500, detail=str(exc)) from exc

    def build_idempotency_key(
        self,
        *,
        event_name: str,
        booking_id: str,
        revision_id: str | None,
        timestamp: str,
    ) -> str:
        raw = "|".join([event_name, booking_id, revision_id or "", timestamp or ""])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def has_processed_event(self, idempotency_key: str) -> bool:
        store = self.read_idempotency_store()
        return bool(store.get(idempotency_key))

    def mark_processed(self, idempotency_key: str, normalized: dict[str, Any]) -> None:
        store = self.read_idempotency_store()
        store[idempotency_key] = {
            "processed_at": self._now_iso(),
            "booking_id": normalized.get("booking_id"),
            "revision_id": normalized.get("revision_id"),
            "channel": normalized.get("destination", {}).get("channel"),
        }
        self.idempotency_store_file.write_text(json.dumps(store, indent=2), encoding="utf-8")

    def read_idempotency_store(self) -> dict[str, Any]:
        if not self.idempotency_store_file.exists():
            return {}
        try:
            return json.loads(self.idempotency_store_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def write_raw_webhook_log(self, entry: dict[str, Any]) -> None:
        booking_id = entry.get("booking_id") or "unknown"
        file_name = f"{int(datetime.now(timezone.utc).timestamp() * 1000)}-{booking_id}.json"
        target = self.raw_log_dir / file_name
        target.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")

    def _pick_string(self, *values: Any) -> str | None:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _safe_json_parse(self, value: str | None, fallback: Any) -> Any:
        if not value:
            return fallback
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback

    def _safe_json_file_parse(self, file_path: str | None, fallback: Any) -> Any:
        if not file_path:
            return fallback
        try:
            target = self._resolve_project_path(file_path)
            if not target.exists():
                return fallback
            return json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return fallback

    def _read_channex_env_file(self) -> dict[str, str]:
        if not self.channex_env_file.exists():
            return {}
        values: dict[str, str] = {}
        try:
            for raw_line in self.channex_env_file.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
        except OSError:
            return {}
        return values

    def _get_env_value(self, key: str, default: str = "") -> str:
        direct = os.getenv(key)
        if direct is not None and str(direct).strip() != "":
            return str(direct).strip()
        file_values = self._read_channex_env_file()
        if key in file_values and file_values[key].strip() != "":
            return file_values[key].strip()
        return default

    def _format_bearer_token(self, token: str) -> str:
        cleaned = token.strip()
        if not cleaned:
            return ""
        if cleaned.lower().startswith("bearer "):
            return cleaned
        return f"Bearer {cleaned}"

    def _read_channex_token_state(self, state_file: str) -> dict[str, str]:
        path = self._resolve_project_path(state_file)
        if not path.exists():
            return {}
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

        auth_token = self._pick_string(parsed.get("authToken"), parsed.get("auth_token"))
        refresh_token = self._pick_string(parsed.get("refreshToken"), parsed.get("refresh_token"))
        return {
            "auth_token": auth_token,
            "refresh_token": refresh_token,
        }

    def write_channex_token_state(self, *, auth_token: str, refresh_token: str, runtime: dict[str, Any]) -> None:
        path = self._resolve_project_path(runtime["channex_token_state_file"])
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "authToken": auth_token,
            "refreshToken": refresh_token,
            "updated_at": self._now_iso(),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _get_runtime_config(self) -> dict[str, Any]:
        timeout_raw = self._get_env_value("CHANNEX_REQUEST_TIMEOUT_SECONDS", "20")
        try:
            request_timeout_seconds = max(int(timeout_raw), 1)
        except (TypeError, ValueError):
            request_timeout_seconds = 20

        booking_channel_map_raw = self._get_env_value("BOOKING_CHANNEL_MAP_JSON", "{}")
        property_map_raw = self._get_env_value("CHANNEX_PROPERTY_MAP_JSON", "{}")
        property_map_file = self._get_env_value("CHANNEX_PROPERTY_MAP_FILE", "./hotelmap.json")
        property_map = self._safe_json_parse(property_map_raw, None)
        if not isinstance(property_map, dict) or not property_map:
            property_map = self._safe_json_file_parse(property_map_file, {})
        if isinstance(property_map, dict) and isinstance(property_map.get("properties"), dict):
            property_map = property_map["properties"]

        token_state_file = self._get_env_value("CHANNEX_TOKEN_STATE_FILE", "./data/channex-token-state.json")
        token_state = self._read_channex_token_state(token_state_file)
        channex_bearer_token = token_state.get("auth_token") or self._get_env_value("CHANNEX_BEARER_TOKEN", "")
        channex_refresh_token = token_state.get("refresh_token") or self._get_env_value("CHANNEX_REFRESH_TOKEN", "")

        return {
            "channex_api_base_url": self._get_env_value("CHANNEX_API_BASE_URL", "").rstrip("/"),
            "channex_app_api_base_url": self._get_env_value(
                "CHANNEX_APP_API_BASE_URL", "https://app.channex.io/api/v1"
            ).rstrip("/"),
            "channex_api_key": self._get_env_value("CHANNEX_API_KEY", ""),
            "channex_bearer_token": channex_bearer_token,
            "channex_refresh_token": channex_refresh_token,
            "channex_token_state_file": token_state_file,
            "channex_webhook_secret": self._get_env_value("CHANNEX_WEBHOOK_SECRET", ""),
            "channex_event_mask": self._get_env_value(
                "CHANNEX_EVENT_MASK", "booking;booking_new;booking_modification;booking_cancellation"
            ),
            "channex_send_data": self._get_env_value("CHANNEX_SEND_DATA", "true").lower()
            in {"true", "1", "yes", "on"},
            "channex_is_global": self._get_env_value("CHANNEX_IS_GLOBAL", "true").lower()
            in {"true", "1", "yes", "on"},
            "channex_property_id": self._get_env_value("CHANNEX_PROPERTY_ID", "") or None,
            "channex_realtime_passthrough_mode": self._get_env_value(
                "CHANNEX_REALTIME_PASSTHROUGH_MODE", "true"
            ).lower()
            in {"true", "1", "yes", "on"},
            "n8n_forward_webhook_url": self._get_env_value("N8N_FORWARD_WEBHOOK_URL", ""),
            "n8n_forward_webhook_token": self._get_env_value("N8N_FORWARD_WEBHOOK_TOKEN", ""),
            "request_timeout_seconds": request_timeout_seconds,
            "booking_channel_map": self._safe_json_parse(booking_channel_map_raw, {}),
            "channex_property_map": property_map,
        }

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()
