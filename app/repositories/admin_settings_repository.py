import os
import json
from uuid import UUID
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


REVIEW_AI_DEFAULT_BASE_URL = "https://r7dnyxy.abc-tunnel.us/v1"
REVIEW_AI_DEFAULT_MODEL = "cx/gpt-5.4-mini-review"
REVIEW_AI_DEFAULT_TIMEOUT_MS = "45000"
CHANNEX_DEFAULT_REQUEST_TIMEOUT_SECONDS = "20"
REVIEW_RATING_DEFAULT_AVERAGE_MIN = "7"
REVIEW_RATING_DEFAULT_GOOD_MIN = "9"
CHATBOT_DEFAULT_LANGUAGE = "vi"
CHATBOT_DEFAULT_CONFIDENCE_THRESHOLD = "0.85"
CHATBOT_DEFAULT_HANDOFF_THRESHOLD = "0.65"
CHATBOT_DEFAULT_CHUNK_SIZE = "1200"
CHATBOT_DEFAULT_CHUNK_OVERLAP = "180"
CHATBOT_DEFAULT_RETRIEVAL_TOP_K = "6"
DEFAULT_AI_PROVIDER_REGISTRY = json.dumps(
    [
        {
            "id": "review-ai-primary",
            "name": "Review AI Primary",
            "apiKey": os.getenv("REVIEW_AI_API_KEY", ""),
            "baseUrl": os.getenv("REVIEW_AI_BASE_URL", REVIEW_AI_DEFAULT_BASE_URL),
            "model": os.getenv("REVIEW_AI_MODEL", REVIEW_AI_DEFAULT_MODEL),
            "timeoutMs": int(os.getenv("REVIEW_AI_TIMEOUT_MS", REVIEW_AI_DEFAULT_TIMEOUT_MS)),
            "services": ["review_insights", "review_translation"],
            "enabled": True,
            "isDefault": True,
        }
    ],
    ensure_ascii=False,
)
DEFAULT_REVIEW_AI_CONNECTION_CONFIG = json.dumps(
    {
        "provider": "review_ai",
        "base_url_setting_key": "review_ai.base_url",
        "api_key_setting_key": "review_ai.api_key",
        "model_setting_key": "review_ai.model",
        "timeout_setting_key": "review_ai.timeout_ms",
    },
    ensure_ascii=False,
)
DEFAULT_TRANSLATION_CONNECTION_CONFIG = json.dumps(
    {
        "provider": "translation",
        "base_url_setting_key": "review_ai.base_url",
        "api_key_setting_key": "review_ai.api_key",
        "model_setting_key": "review_ai.model",
        "timeout_setting_key": "review_ai.timeout_ms",
        "note": "Tạm dùng chung hạ tầng AI hiện tại cho dịch và phân tích.",
    },
    ensure_ascii=False,
)
DEFAULT_LARK_BAD_REVIEW_CONNECTION_CONFIG = json.dumps(
    {
        "provider": "lark",
        "webhook_setting_key": "notification.lark_bad_review_webhook_url",
        "timeout_setting_key": "notification.lark_timeout_seconds",
    },
    ensure_ascii=False,
)
DEFAULT_LARK_HANDOFF_CONNECTION_CONFIG = json.dumps(
    {
        "provider": "lark",
        "webhook_setting_key": "notification.lark_handoff_webhook_url",
        "timeout_setting_key": "notification.lark_timeout_seconds",
    },
    ensure_ascii=False,
)
CHATBOT_DEFAULT_BUSINESS_HOURS = json.dumps(
    {
        "timezone": "Asia/Bangkok",
        "days": {
            "mon": [{"from": "08:00", "to": "22:00"}],
            "tue": [{"from": "08:00", "to": "22:00"}],
            "wed": [{"from": "08:00", "to": "22:00"}],
            "thu": [{"from": "08:00", "to": "22:00"}],
            "fri": [{"from": "08:00", "to": "22:00"}],
            "sat": [{"from": "08:00", "to": "22:00"}],
            "sun": [{"from": "08:00", "to": "22:00"}],
        },
    },
    ensure_ascii=True,
)


def build_default_setting_definitions() -> list[dict[str, Any]]:
    return [
        {
            "setting_key": "integrations.channex_api_base_url",
            "group_code": "integrations",
            "label": "Channex API base URL",
            "description": "Base URL de webhook receiver goi sang Channex bookings API.",
            "value_text": os.getenv("CHANNEX_API_BASE_URL", ""),
            "value_type": "url",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "integrations.channex_api_key",
            "group_code": "integrations",
            "label": "Channex API key",
            "description": "API key dung de lay chi tiet booking tu Channex sau khi webhook ban trigger.",
            "value_text": os.getenv("CHANNEX_API_KEY", ""),
            "value_type": "secret",
            "is_secret": True,
            "is_editable": True,
        },
        {
            "setting_key": "integrations.channex_webhook_secret",
            "group_code": "integrations",
            "label": "Channex webhook secret",
            "description": "Secret header X-Channex-Webhook-Secret de xac thuc webhook tu Channex.",
            "value_text": os.getenv("CHANNEX_WEBHOOK_SECRET", ""),
            "value_type": "secret",
            "is_secret": True,
            "is_editable": True,
        },
        {
            "setting_key": "integrations.channex_request_timeout_seconds",
            "group_code": "integrations",
            "label": "Channex request timeout (seconds)",
            "description": "Timeout cho request webhook bridge goi Channex hoac n8n.",
            "value_text": os.getenv(
                "CHANNEX_REQUEST_TIMEOUT_SECONDS",
                CHANNEX_DEFAULT_REQUEST_TIMEOUT_SECONDS,
            ),
            "value_type": "integer",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "integrations.channex_n8n_forward_webhook_url",
            "group_code": "integrations",
            "label": "Channex n8n forward webhook URL",
            "description": "Webhook dich de backend day du lieu booking da normalize sang n8n.",
            "value_text": os.getenv("N8N_FORWARD_WEBHOOK_URL", ""),
            "value_type": "url",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "integrations.channex_n8n_forward_webhook_token",
            "group_code": "integrations",
            "label": "Channex n8n forward webhook token",
            "description": "Token header X-Bridge-Token khi day booking bridge sang n8n.",
            "value_text": os.getenv("N8N_FORWARD_WEBHOOK_TOKEN", ""),
            "value_type": "secret",
            "is_secret": True,
            "is_editable": True,
        },
        {
            "setting_key": "integrations.channex_booking_channel_map_json",
            "group_code": "integrations",
            "label": "Channex booking channel map JSON",
            "description": "JSON map nguon booking sang destination channel de webhook bridge chuyen tiep.",
            "value_text": os.getenv("BOOKING_CHANNEL_MAP_JSON", "{}"),
            "value_type": "json",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "ai.providers_registry",
            "group_code": "ai",
            "label": "AI providers registry",
            "description": "List of AI providers and the services mapped to each provider.",
            "value_text": DEFAULT_AI_PROVIDER_REGISTRY,
            "value_type": "json",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "connections.review_ai_primary",
            "group_code": "connections",
            "label": "Kết nối AI chính",
            "description": "Cấu hình kết nối AI mặc định. Chỉ tham chiếu sang các key secret đang lưu sẵn, không lưu secret lặp lại.",
            "value_text": DEFAULT_REVIEW_AI_CONNECTION_CONFIG,
            "value_type": "json",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "connections.translation_primary",
            "group_code": "connections",
            "label": "Kết nối dịch mặc định",
            "description": "Kết nối dùng cho dịch nội dung review hoặc chatbot. Có thể trỏ sang cùng nhà cung cấp AI hiện tại.",
            "value_text": DEFAULT_TRANSLATION_CONNECTION_CONFIG,
            "value_type": "json",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "connections.lark_bad_review_primary",
            "group_code": "connections",
            "label": "Kết nối Lark bad review",
            "description": "Kết nối mặc định dùng để gửi bad review sang Lark.",
            "value_text": DEFAULT_LARK_BAD_REVIEW_CONNECTION_CONFIG,
            "value_type": "json",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "connections.lark_handoff_primary",
            "group_code": "connections",
            "label": "Kết nối Lark handoff",
            "description": "Kết nối mặc định dùng để gửi handoff chatbot sang Lark.",
            "value_text": DEFAULT_LARK_HANDOFF_CONNECTION_CONFIG,
            "value_type": "json",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "service_bindings.review_insights_connection",
            "group_code": "service_bindings",
            "label": "Dịch vụ Review Insights",
            "description": "Setting key của kết nối đang được Review Insights sử dụng.",
            "value_text": "connections.review_ai_primary",
            "value_type": "string",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "service_bindings.review_translation_connection",
            "group_code": "service_bindings",
            "label": "Dịch vụ dịch review",
            "description": "Setting key của kết nối đang dùng để dịch review và nội dung liên quan.",
            "value_text": "connections.translation_primary",
            "value_type": "string",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "service_bindings.bad_review_lark_connection",
            "group_code": "service_bindings",
            "label": "Dịch vụ gửi bad review",
            "description": "Setting key của kết nối đang dùng để gửi bad review sang Lark.",
            "value_text": "connections.lark_bad_review_primary",
            "value_type": "string",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "service_bindings.chatbot_handoff_lark_connection",
            "group_code": "service_bindings",
            "label": "Dịch vụ handoff chatbot",
            "description": "Setting key của kết nối đang dùng để chuyển handoff chatbot sang Lark.",
            "value_text": "connections.lark_handoff_primary",
            "value_type": "string",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "review.rating_band_average_min",
            "group_code": "review",
            "label": "Average review min score",
            "description": "Nguong diem toi thieu de xep review vao nhom Average tren thang 10.",
            "value_text": os.getenv(
                "REVIEW_RATING_BAND_AVERAGE_MIN",
                REVIEW_RATING_DEFAULT_AVERAGE_MIN,
            ),
            "value_type": "float",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "review.rating_band_good_min",
            "group_code": "review",
            "label": "Good review min score",
            "description": "Nguong diem toi thieu de xep review vao nhom Good tren thang 10.",
            "value_text": os.getenv(
                "REVIEW_RATING_BAND_GOOD_MIN",
                REVIEW_RATING_DEFAULT_GOOD_MIN,
            ),
            "value_type": "float",
            "is_secret": False,
            "is_editable": True,
        },
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
            "setting_key": "chatbot.enabled",
            "group_code": "chatbot",
            "label": "Chatbot enabled",
            "description": "Bat hoac tat toan bo luong chatbot trong admin runtime.",
            "value_text": os.getenv("CHATBOT_ENABLED", "false"),
            "value_type": "boolean",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "chatbot.default_language",
            "group_code": "chatbot",
            "label": "Chatbot default language",
            "description": "Ngon ngu mac dinh bot dung de tra loi khi chua du doan duoc ngon ngu khach.",
            "value_text": os.getenv("CHATBOT_DEFAULT_LANGUAGE", CHATBOT_DEFAULT_LANGUAGE),
            "value_type": "string",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "chatbot.confidence_threshold",
            "group_code": "chatbot",
            "label": "Chatbot confidence threshold",
            "description": "Nguong confidence de bot duoc phep auto reply.",
            "value_text": os.getenv("CHATBOT_CONFIDENCE_THRESHOLD", CHATBOT_DEFAULT_CONFIDENCE_THRESHOLD),
            "value_type": "float",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "chatbot.handoff_threshold",
            "group_code": "chatbot",
            "label": "Chatbot handoff threshold",
            "description": "Neu confidence thap hon nguong nay thi handoff sang nguoi that.",
            "value_text": os.getenv("CHATBOT_HANDOFF_THRESHOLD", CHATBOT_DEFAULT_HANDOFF_THRESHOLD),
            "value_type": "float",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "chatbot.allow_after_hours_reply",
            "group_code": "chatbot",
            "label": "Allow after-hours reply",
            "description": "Cho phep bot tra loi ngoai gio hanh chinh neu knowledge du an toan.",
            "value_text": os.getenv("CHATBOT_ALLOW_AFTER_HOURS_REPLY", "true"),
            "value_type": "boolean",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "chatbot.allow_price_quote",
            "group_code": "chatbot",
            "label": "Allow price quote",
            "description": "Chi bat khi da co runtime source gia that va da test on dinh.",
            "value_text": os.getenv("CHATBOT_ALLOW_PRICE_QUOTE", "false"),
            "value_type": "boolean",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "chatbot.allow_inventory_lookup",
            "group_code": "chatbot",
            "label": "Allow inventory lookup",
            "description": "Chi bat khi da co runtime source ton phong production.",
            "value_text": os.getenv("CHATBOT_ALLOW_INVENTORY_LOOKUP", "false"),
            "value_type": "boolean",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "chatbot.allow_booking_status_lookup",
            "group_code": "chatbot",
            "label": "Allow booking status lookup",
            "description": "Chi bat khi da co runtime source booking status production.",
            "value_text": os.getenv("CHATBOT_ALLOW_BOOKING_STATUS_LOOKUP", "false"),
            "value_type": "boolean",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "chatbot.business_hours_json",
            "group_code": "chatbot",
            "label": "Business hours JSON",
            "description": "Khung gio hanh chinh de bot va handoff dung chung.",
            "value_text": os.getenv("CHATBOT_BUSINESS_HOURS_JSON", CHATBOT_DEFAULT_BUSINESS_HOURS),
            "value_type": "json",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "rag.auto_sync_enabled",
            "group_code": "rag",
            "label": "RAG auto sync enabled",
            "description": "Tu dong sync knowledge publish sang knowledge documents khi bat.",
            "value_text": os.getenv("RAG_AUTO_SYNC_ENABLED", "false"),
            "value_type": "boolean",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "rag.chunk_size",
            "group_code": "rag",
            "label": "RAG chunk size",
            "description": "Do dai chunk mac dinh khi cat knowledge cho retrieval.",
            "value_text": os.getenv("RAG_CHUNK_SIZE", CHATBOT_DEFAULT_CHUNK_SIZE),
            "value_type": "integer",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "rag.chunk_overlap",
            "group_code": "rag",
            "label": "RAG chunk overlap",
            "description": "So ky tu overlap giua cac chunk de giu ngu canh.",
            "value_text": os.getenv("RAG_CHUNK_OVERLAP", CHATBOT_DEFAULT_CHUNK_OVERLAP),
            "value_type": "integer",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "rag.retrieval_top_k",
            "group_code": "rag",
            "label": "RAG retrieval top K",
            "description": "So luong chunk toi da tra ve cho moi truy van.",
            "value_text": os.getenv("RAG_RETRIEVAL_TOP_K", CHATBOT_DEFAULT_RETRIEVAL_TOP_K),
            "value_type": "integer",
            "is_secret": False,
            "is_editable": True,
        },
        {
            "setting_key": "rag.reindex_on_publish",
            "group_code": "rag",
            "label": "Reindex on publish",
            "description": "Neu bat, backend se uu tien re-index lai document khi knowledge moi duoc publish.",
            "value_text": os.getenv("RAG_REINDEX_ON_PUBLISH", "true"),
            "value_type": "boolean",
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
        {
            "setting_key": "notification.lark_handoff_webhook_url",
            "group_code": "notifications",
            "label": "Lark handoff webhook",
            "description": "Webhook mac dinh de gui handoff cua chatbot sang Lark.",
            "value_text": os.getenv("LARK_HANDOFF_WEBHOOK_URL", ""),
            "value_type": "secret",
            "is_secret": True,
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
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        self.db.execute(text("ALTER TABLE system_settings DROP CONSTRAINT IF EXISTS chk_system_settings_value_type"))
        self.db.execute(
            text(
                """
                ALTER TABLE system_settings
                ADD CONSTRAINT chk_system_settings_value_type CHECK (
                    value_type IN ('string', 'secret', 'url', 'integer', 'float', 'boolean', 'json')
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
