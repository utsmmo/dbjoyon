import os
from uuid import UUID
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


REVIEW_AI_DEFAULT_BASE_URL = "https://r7dnyxy.abc-tunnel.us/v1"
REVIEW_AI_DEFAULT_MODEL = "cx/gpt-5.4-mini-review"
REVIEW_AI_DEFAULT_TIMEOUT_MS = "45000"


def build_default_setting_definitions() -> list[dict[str, Any]]:
    return [
        {
            "setting_key": "review_ai.base_url",
            "group_code": "ai",
            "label": "Review AI base URL",
            "description": "Endpoint chat completions dung cho AI review insights.",
            "value_text": os.getenv("REVIEW_AI_BASE_URL", REVIEW_AI_DEFAULT_BASE_URL),
            "value_type": "url",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "review_ai.api_key",
            "group_code": "ai",
            "label": "Review AI API key",
            "description": "API key dung de goi AI review insights.",
            "value_text": os.getenv("REVIEW_AI_API_KEY", ""),
            "value_type": "secret",
            "is_secret": True,
            "is_editable": True,
        },
        {
            "setting_key": "review_ai.model",
            "group_code": "ai",
            "label": "Review AI model",
            "description": "Model duoc dung de sinh nhan dinh review.",
            "value_text": os.getenv("REVIEW_AI_MODEL", REVIEW_AI_DEFAULT_MODEL),
            "value_type": "string",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "review_ai.timeout_ms",
            "group_code": "ai",
            "label": "Review AI timeout (ms)",
            "description": "Thoi gian timeout cho mot request AI.",
            "value_text": os.getenv("REVIEW_AI_TIMEOUT_MS", REVIEW_AI_DEFAULT_TIMEOUT_MS),
            "value_type": "integer",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "notification.lark_bad_review_webhook_url",
            "group_code": "notifications",
            "label": "Lark bad review webhook",
            "description": "Webhook mac dinh de day bad review sang Lark.",
            "value_text": os.getenv("LARK_BAD_REVIEW_WEBHOOK_URL", ""),
            "value_type": "secret",
            "is_secret": True,
            "is_editable": True,
        },
        {
            "setting_key": "notification.lark_timeout_seconds",
            "group_code": "notifications",
            "label": "Lark timeout (seconds)",
            "description": "Timeout khi goi webhook Lark.",
            "value_text": os.getenv("LARK_NOTIFICATION_TIMEOUT_SECONDS", "15"),
            "value_type": "integer",
            "is_secret": False,
            "is_editable": True,
        },
    ]


class AdminSettingsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_settings_schema(self) -> None:
        self.db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS system_settings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    setting_key VARCHAR(120) NOT NULL UNIQUE,
                    group_code VARCHAR(60) NOT NULL,
                    label VARCHAR(120) NOT NULL,
                    description TEXT,
                    value_text TEXT,
                    value_type VARCHAR(30) NOT NULL DEFAULT 'string',
                    is_secret BOOLEAN NOT NULL DEFAULT FALSE,
                    is_editable BOOLEAN NOT NULL DEFAULT TRUE,
                    updated_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT chk_system_settings_value_type CHECK (
                        value_type IN ('string', 'secret', 'url', 'integer')
                    )
                )
                """
            )
        )
        self.db.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_system_settings_group_code
                    ON system_settings (group_code, setting_key)
                """
            )
        )

    def ensure_settings_baseline(self) -> None:
        self.ensure_settings_schema()
        for setting in build_default_setting_definitions():
            self.db.execute(
                text(
                    """
                    INSERT INTO system_settings (
                        setting_key,
                        group_code,
                        label,
                        description,
                        value_text,
                        value_type,
                        is_secret,
                        is_editable
                    )
                    VALUES (
                        :setting_key,
                        :group_code,
                        :label,
                        :description,
                        :value_text,
                        :value_type,
                        :is_secret,
                        :is_editable
                    )
                    ON CONFLICT (setting_key) DO UPDATE
                    SET
                        group_code = EXCLUDED.group_code,
                        label = EXCLUDED.label,
                        description = EXCLUDED.description,
                        value_type = EXCLUDED.value_type,
                        is_secret = EXCLUDED.is_secret,
                        is_editable = EXCLUDED.is_editable
                    """
                ),
                setting,
            )

    def list_settings(self) -> list[dict[str, Any]]:
        result = self.db.execute(
            text(
                """
                SELECT
                    s.id::text AS id,
                    s.setting_key,
                    s.group_code,
                    s.label,
                    s.description,
                    s.value_text,
                    s.value_type,
                    s.is_secret,
                    s.is_editable,
                    s.updated_by_user_id::text AS updated_by_user_id,
                    u.email AS updated_by_email,
                    s.created_at,
                    s.updated_at
                FROM system_settings s
                LEFT JOIN users u ON u.id = s.updated_by_user_id
                ORDER BY s.group_code ASC, s.setting_key ASC
                """
            )
        )
        return [dict(row) for row in result.mappings().all()]

    def get_setting_values(self, setting_keys: list[str] | None = None) -> dict[str, str | None]:
        rows = self.list_settings()
        values = {
            row["setting_key"]: row.get("value_text")
            for row in rows
        }
        if setting_keys is None:
            return values
        return {key: values.get(key) for key in setting_keys}

    def update_setting(
        self,
        *,
        setting_key: str,
        value_text: str | None,
        updated_by_user_id: str | None,
    ) -> dict[str, Any] | None:
        normalized_user_id: str | None = None
        if updated_by_user_id:
            normalized_user_id = str(UUID(updated_by_user_id.strip()))

        payload = {
            "setting_key": setting_key,
            "value_text": value_text,
            "updated_by_user_id": normalized_user_id,
        }
        result = self.db.execute(
            text(
                """
                UPDATE system_settings
                SET
                    value_text = :value_text,
                    updated_at = NOW(),
                    updated_by_user_id = :updated_by_user_id
                WHERE setting_key = :setting_key
                  AND is_editable = TRUE
                RETURNING
                    id::text AS id,
                    setting_key,
                    group_code,
                    label,
                    description,
                    value_text,
                    value_type,
                    is_secret,
                    is_editable,
                    updated_by_user_id::text AS updated_by_user_id,
                    (
                        SELECT email
                        FROM users
                        WHERE id = system_settings.updated_by_user_id
                    ) AS updated_by_email,
                    created_at,
                    updated_at
                """
            ),
            payload,
        )
        row = result.mappings().first()
        if row is None:
            return None

        return dict(row)
