from sqlalchemy import text
from sqlalchemy.orm import Session

SUPPORTED_REVIEW_PLATFORMS: dict[str, str] = {
    "booking": "Booking.com",
    "agoda": "Agoda",
    "ctrip": "Ctrip",
    "expedia": "Expedia",
    "tripadvisor": "Tripadvisor",
    "google": "Google Reviews",
}


class PlatformRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_platform_by_code(self, platform_code: str) -> dict | None:
        result = self.db.execute(
            text(
                """
                SELECT id::text AS id, platform_code
                FROM platforms
                WHERE platform_code = :platform_code
                  AND is_active = TRUE
                """
            ),
            {"platform_code": platform_code},
        )
        row = result.mappings().first()
        if row is None and platform_code in SUPPORTED_REVIEW_PLATFORMS:
            self.ensure_platform(platform_code)
            result = self.db.execute(
                text(
                    """
                    SELECT id::text AS id, platform_code
                    FROM platforms
                    WHERE platform_code = :platform_code
                      AND is_active = TRUE
                    """
                ),
                {"platform_code": platform_code},
            )
            row = result.mappings().first()
        return dict(row) if row else None

    def ensure_platform(self, platform_code: str) -> None:
        platform_name = SUPPORTED_REVIEW_PLATFORMS.get(platform_code)
        if not platform_name:
            return

        self.db.execute(
            text(
                """
                INSERT INTO platforms (platform_code, platform_name, platform_type, is_active, metadata)
                VALUES (
                    :platform_code,
                    :platform_name,
                    'review',
                    TRUE,
                    CAST(:metadata AS jsonb)
                )
                ON CONFLICT (platform_code) DO UPDATE
                SET
                    platform_name = EXCLUDED.platform_name,
                    platform_type = EXCLUDED.platform_type,
                    is_active = EXCLUDED.is_active,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                """
            ),
            {
                "platform_code": platform_code,
                "platform_name": platform_name,
                "metadata": '{"source":"runtime-bootstrap"}',
            },
        )
