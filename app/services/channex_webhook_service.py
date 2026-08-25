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

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.repositories.admin_settings_repository import AdminSettingsRepository


@dataclass
class ChannexWebhookError(Exception):
    code: str
    status_code: int
    detail: Any | None = None

    def __str__(self) -> str:
        return self.code


class ChannexWebhookService:
    def __init__(self) -> None:
        self.idempotency_store_file = Path(
            os.getenv("CHANNEX_IDEMPOTENCY_STORE_FILE", "./data/channex-processed-events.json")
        ).resolve()
        self.raw_log_dir = Path(os.getenv("CHANNEX_RAW_LOG_DIR", "./data/channex-raw-events")).resolve()

        self.idempotency_store_file.parent.mkdir(parents=True, exist_ok=True)
        self.raw_log_dir.mkdir(parents=True, exist_ok=True)

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

        if not event_name or not booking_id:
            raise ChannexWebhookError(
                code="invalid_payload",
                status_code=400,
                detail={
                    "required_fields": ["event", "booking_id"],
                    "received_shape": self.summarize_webhook_payload(payload),
                },
            )

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
        phone_raw = self._pick_string(customer.get("phone"))

        return {
            "source": "channex",
            "event": str(webhook_payload.get("event") or webhook_payload.get("type") or ""),
            "timestamp": self._pick_string(webhook_payload.get("timestamp")) or received_at,
            "received_at": received_at,
            "idempotency_key": idempotency_key,
            "property_id": property_id,
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

    def resolve_destination(self, source_domain: str, *, booking_channel_map: dict[str, Any]) -> dict[str, Any]:
        if isinstance(booking_channel_map.get(source_domain), dict):
            return booking_channel_map[source_domain]
        if isinstance(booking_channel_map.get("default"), dict):
            return booking_channel_map["default"]
        return {
            "channel": "manual_review",
            "reason": f"No mapping for source_domain={source_domain}",
        }

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

    def _get_runtime_config(self) -> dict[str, Any]:
        keys = [
            "integrations.channex_api_base_url",
            "integrations.channex_api_key",
            "integrations.channex_webhook_secret",
            "integrations.channex_n8n_forward_webhook_url",
            "integrations.channex_n8n_forward_webhook_token",
            "integrations.channex_request_timeout_seconds",
            "integrations.channex_booking_channel_map_json",
        ]
        db_values = self._load_setting_values(keys)

        timeout_raw = (
            db_values.get("integrations.channex_request_timeout_seconds")
            or os.getenv("CHANNEX_REQUEST_TIMEOUT_SECONDS")
            or "20"
        )
        try:
            request_timeout_seconds = max(int(timeout_raw), 1)
        except (TypeError, ValueError):
            request_timeout_seconds = 20

        booking_channel_map_raw = (
            db_values.get("integrations.channex_booking_channel_map_json")
            or os.getenv("BOOKING_CHANNEL_MAP_JSON")
            or "{}"
        )

        return {
            "channex_api_base_url": str(
                db_values.get("integrations.channex_api_base_url")
                or os.getenv("CHANNEX_API_BASE_URL")
                or ""
            ).rstrip("/"),
            "channex_api_key": str(
                db_values.get("integrations.channex_api_key")
                or os.getenv("CHANNEX_API_KEY")
                or ""
            ).strip(),
            "channex_webhook_secret": str(
                db_values.get("integrations.channex_webhook_secret")
                or os.getenv("CHANNEX_WEBHOOK_SECRET")
                or ""
            ).strip(),
            "n8n_forward_webhook_url": str(
                db_values.get("integrations.channex_n8n_forward_webhook_url")
                or os.getenv("N8N_FORWARD_WEBHOOK_URL")
                or ""
            ).strip(),
            "n8n_forward_webhook_token": str(
                db_values.get("integrations.channex_n8n_forward_webhook_token")
                or os.getenv("N8N_FORWARD_WEBHOOK_TOKEN")
                or ""
            ).strip(),
            "request_timeout_seconds": request_timeout_seconds,
            "booking_channel_map": self._safe_json_parse(booking_channel_map_raw, {}),
        }

    def _load_setting_values(self, keys: list[str]) -> dict[str, str | None]:
        try:
            with SessionLocal() as db:
                settings_table_exists = bool(
                    db.execute(
                        text("SELECT to_regclass('public.system_settings') IS NOT NULL")
                    ).scalar()
                )
                if not settings_table_exists:
                    return {}
                repository = AdminSettingsRepository(db)
                return repository.get_setting_values(keys)
        except SQLAlchemyError:
            return {}

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()
