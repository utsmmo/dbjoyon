from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories._json import to_jsonb_param


class IncidentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_bad_review_incident(
        self,
        *,
        hotel_id: str,
        review_id: str,
        title: str,
        description: str | None,
        metadata: dict[str, Any],
    ) -> bool:
        existing = self.db.execute(
            text(
                """
                SELECT id
                FROM incidents
                WHERE review_id = CAST(:review_id AS uuid)
                  AND incident_type = 'bad_review'
                  AND status IN ('open', 'triaged', 'in_progress')
                LIMIT 1
                """
            ),
            {"review_id": review_id},
        ).first()

        if existing:
            return False

        self.db.execute(
            text(
                """
                INSERT INTO incidents (
                    hotel_id,
                    review_id,
                    incident_type,
                    severity,
                    status,
                    title,
                    description,
                    metadata
                )
                VALUES (
                    CAST(:hotel_id AS uuid),
                    CAST(:review_id AS uuid),
                    'bad_review',
                    :severity,
                    'open',
                    :title,
                    :description,
                    CAST(:metadata AS jsonb)
                )
                """
            ),
            {
                "hotel_id": hotel_id,
                "review_id": review_id,
                "severity": metadata.get("severity", "high"),
                "title": title,
                "description": description,
                "metadata": to_jsonb_param(metadata),
            },
        )
        return True

    def list_incidents(
        self,
        *,
        hotel_id: str | None,
        status: str | None,
        severity: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        filters = ["1 = 1"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if hotel_id:
            filters.append("hotel_id = CAST(:hotel_id AS uuid)")
            params["hotel_id"] = hotel_id
        if status:
            filters.append("status = :status")
            params["status"] = status
        if severity:
            filters.append("severity = :severity")
            params["severity"] = severity

        where_clause = " AND ".join(filters)

        query = text(
            f"""
            SELECT
                id::text AS id,
                hotel_id::text AS hotel_id,
                review_id::text AS review_id,
                incident_type,
                severity,
                status,
                title,
                description,
                detected_at,
                resolved_at,
                owner_name,
                metadata,
                COUNT(*) OVER() AS total_count
            FROM incidents
            WHERE {where_clause}
            ORDER BY detected_at DESC, created_at DESC
            LIMIT :limit OFFSET :offset
            """
        )
        rows = self.db.execute(query, params).mappings().all()
        total = int(rows[0]["total_count"]) if rows else 0
        items = [{k: v for k, v in row.items() if k != "total_count"} for row in rows]
        return items, total
