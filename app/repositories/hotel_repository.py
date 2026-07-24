from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories._json import to_jsonb_param


class HotelRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_hotel(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.db.execute(
            text(
                """
                INSERT INTO hotels (
                    hotel_code,
                    hotel_name,
                    legal_name,
                    timezone,
                    country_code,
                    city,
                    address_line1,
                    address_line2,
                    postal_code,
                    phone,
                    email,
                    status,
                    metadata
                )
                VALUES (
                    :hotel_code,
                    :hotel_name,
                    :legal_name,
                    :timezone,
                    :country_code,
                    :city,
                    :address_line1,
                    :address_line2,
                    :postal_code,
                    :phone,
                    :email,
                    :status,
                    CAST(:metadata AS jsonb)
                )
                RETURNING
                    id::text AS id,
                    hotel_code,
                    hotel_name,
                    legal_name,
                    timezone,
                    country_code,
                    city,
                    address_line1,
                    address_line2,
                    postal_code,
                    phone,
                    email,
                    status,
                    metadata,
                    created_at,
                    updated_at
                """
            ),
            {
                **payload,
                "metadata": to_jsonb_param(payload.get("metadata")),
            },
        )
        return dict(result.mappings().one())

    def list_hotels(
        self,
        *,
        q: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        filters = ["1 = 1"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if q:
            filters.append(
                "(hotel_code ILIKE :q OR hotel_name ILIKE :q OR city ILIKE :q)"
            )
            params["q"] = f"%{q}%"
        if status:
            filters.append("status = :status")
            params["status"] = status

        where_clause = " AND ".join(filters)

        result = self.db.execute(
            text(
                f"""
                SELECT
                    id::text AS id,
                    hotel_code,
                    hotel_name,
                    legal_name,
                    timezone,
                    country_code,
                    city,
                    address_line1,
                    address_line2,
                    postal_code,
                    phone,
                    email,
                    status,
                    metadata,
                    created_at,
                    updated_at,
                    COUNT(*) OVER() AS total_count
                FROM hotels
                WHERE {where_clause}
                ORDER BY hotel_name ASC, created_at ASC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        )
        rows = result.mappings().all()
        total = int(rows[0]["total_count"]) if rows else 0
        items = [{k: v for k, v in row.items() if k != "total_count"} for row in rows]
        return items, total

    def list_export_hotels(
        self,
        *,
        hotel_ids: list[str] | None,
        only_active_hotels: bool,
    ) -> list[dict[str, Any]]:
        filters = ["1 = 1"]
        params: dict[str, Any] = {}

        if only_active_hotels:
            filters.append("status = 'active'")

        if hotel_ids:
            filters.append("id::text = ANY(:hotel_ids)")
            params["hotel_ids"] = hotel_ids

        where_clause = " AND ".join(filters)
        result = self.db.execute(
            text(
                f"""
                SELECT
                    id::text AS id,
                    hotel_code,
                    hotel_name,
                    status,
                    metadata
                FROM hotels
                WHERE {where_clause}
                ORDER BY hotel_name ASC
                """
            ),
            params,
        )
        return [dict(row) for row in result.mappings().all()]
