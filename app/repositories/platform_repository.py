from sqlalchemy import text
from sqlalchemy.orm import Session


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
        return dict(row) if row else None
