import os

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.admin_settings_repository import (
    AdminSettingsRepository,
    REVIEW_AI_DEFAULT_BASE_URL,
    REVIEW_AI_DEFAULT_MODEL,
    REVIEW_AI_DEFAULT_TIMEOUT_MS,
)
from app.schemas.admin_settings import (
    AdminSettingListResponse,
    AdminSettingResponse,
    AdminSettingUpdateRequest,
)


class AdminSettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AdminSettingsRepository(db)

    def list_settings(self) -> AdminSettingListResponse:
        try:
            self.repository.ensure_settings_baseline()
            self.db.commit()
            items = [self._serialize_setting(item) for item in self.repository.list_settings()]
            return AdminSettingListResponse(items=items, total=len(items))
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while loading settings") from exc

    def update_setting(
        self,
        *,
        setting_key: str,
        payload: AdminSettingUpdateRequest,
    ) -> AdminSettingResponse:
        try:
            self.repository.ensure_settings_baseline()
            self.db.commit()
            existing = next(
                (item for item in self.repository.list_settings() if item["setting_key"] == setting_key),
                None,
            )
            if existing is None:
                raise ValueError("setting not found")

            normalized_value = self._normalize_value(
                value_type=existing["value_type"],
                value=payload.value,
            )
            updated = self.repository.update_setting(
                setting_key=setting_key,
                value_text=normalized_value,
                updated_by_user_id=payload.updated_by_user_id,
            )
            if updated is None:
                raise ValueError("setting is not editable or does not exist")
            self.db.commit()
            return self._serialize_setting(updated)
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while updating setting") from exc

    def get_review_ai_runtime_config(self) -> dict[str, str | int]:
        try:
            self.repository.ensure_settings_baseline()
            self.db.commit()
            values = self.repository.get_setting_values(
                [
                    "review_ai.base_url",
                    "review_ai.api_key",
                    "review_ai.model",
                    "review_ai.timeout_ms",
                ]
            )
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while loading review AI settings") from exc

        base_url = (
            values.get("review_ai.base_url")
            or os.getenv("REVIEW_AI_BASE_URL")
            or REVIEW_AI_DEFAULT_BASE_URL
        ).strip()
        api_key = (
            values.get("review_ai.api_key")
            or os.getenv("REVIEW_AI_API_KEY")
            or ""
        ).strip()
        model = (
            values.get("review_ai.model")
            or os.getenv("REVIEW_AI_MODEL")
            or REVIEW_AI_DEFAULT_MODEL
        ).strip()
        timeout_raw = (
            values.get("review_ai.timeout_ms")
            or os.getenv("REVIEW_AI_TIMEOUT_MS")
            or REVIEW_AI_DEFAULT_TIMEOUT_MS
        )

        try:
            timeout_ms = max(int(timeout_raw or REVIEW_AI_DEFAULT_TIMEOUT_MS), 1000)
        except (TypeError, ValueError):
            timeout_ms = int(REVIEW_AI_DEFAULT_TIMEOUT_MS)

        return {
            "base_url": base_url,
            "api_key": api_key,
            "model": model,
            "timeout_ms": timeout_ms,
        }

    def _serialize_setting(self, item: dict[str, object]) -> AdminSettingResponse:
        raw_value = str(item.get("value_text") or "")
        is_secret = bool(item.get("is_secret"))
        masked_value = self._mask_secret(raw_value) if is_secret else None
        return AdminSettingResponse(
            id=str(item["id"]),
            setting_key=str(item["setting_key"]),
            group_code=str(item["group_code"]),
            label=str(item["label"]),
            description=str(item.get("description") or "") or None,
            value_type=str(item["value_type"]),
            is_secret=is_secret,
            is_editable=bool(item["is_editable"]),
            value=None if is_secret else raw_value,
            masked_value=masked_value,
            updated_by_user_id=str(item["updated_by_user_id"]) if item.get("updated_by_user_id") else None,
            updated_by_email=str(item["updated_by_email"]) if item.get("updated_by_email") else None,
            created_at=item["created_at"],
            updated_at=item["updated_at"],
        )

    def _normalize_value(self, *, value_type: str, value: str | int | bool | None) -> str | None:
        if value is None:
            return None

        if isinstance(value, bool):
            normalized = "true" if value else "false"
        else:
            normalized = str(value).strip()

        if value_type == "integer":
            try:
                int(normalized)
            except ValueError as exc:
                raise ValueError("setting value must be an integer") from exc
        elif value_type == "url" and normalized and not normalized.startswith(("http://", "https://")):
            raise ValueError("setting value must start with http:// or https://")

        return normalized

    def _mask_secret(self, value: str) -> str | None:
        stripped = value.strip()
        if not stripped:
            return None
        if len(stripped) <= 8:
            return "*" * len(stripped)
        return f"{stripped[:3]}{'*' * max(len(stripped) - 7, 4)}{stripped[-4:]}"
