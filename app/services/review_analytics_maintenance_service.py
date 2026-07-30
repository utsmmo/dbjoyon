from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session


class ReviewAnalyticsMaintenanceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.migrations_dir = Path(__file__).resolve().parents[2] / "db" / "migrations"

    def rebuild_dashboard_analytics(self) -> None:
        for migration_name in (
            "008_review_dashboard_analytics.sql",
            "009_backfill_review_dashboard_analytics.sql",
        ):
            self._execute_migration_script(self.migrations_dir / migration_name)

    def _execute_migration_script(self, path: Path) -> None:
        sql_text = path.read_text(encoding="utf-8")
        for statement in self._split_sql_statements(sql_text):
            self.db.execute(text(statement))

    @staticmethod
    def _split_sql_statements(sql_text: str) -> list[str]:
        statements: list[str] = []
        current_lines: list[str] = []

        for raw_line in sql_text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("--"):
                continue
            if line.upper() in {"BEGIN;", "COMMIT;"}:
                continue

            current_lines.append(raw_line)
            if line.endswith(";"):
                statement = "\n".join(current_lines).strip()
                if statement.endswith(";"):
                    statement = statement[:-1].strip()
                if statement:
                    statements.append(statement)
                current_lines = []

        trailing = "\n".join(current_lines).strip()
        if trailing:
            statements.append(trailing)

        return statements
