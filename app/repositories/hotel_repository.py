from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories._json import to_jsonb_param


class HotelRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_hotel_by_id(self, hotel_id: str) -> dict[str, Any] | None:
        result = self.db.execute(
            text(
                """
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
                    updated_at
                FROM hotels
                WHERE id = CAST(:hotel_id AS uuid)
                """
            ),
            {"hotel_id": hotel_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

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

    def delete_all_hotels(self) -> int:
        result = self.db.execute(
            text(
                """
                DELETE FROM hotels
                RETURNING id
                """
            )
        )
        return len(result.fetchall())

    def create_hotel_platform_account(
        self,
        *,
        hotel_id: str,
        platform_id: str,
        external_account_id: str,
        display_name: str | None,
        config: dict[str, Any],
        raw_payload: dict[str, Any],
    ) -> dict[str, Any]:
        result = self.db.execute(
            text(
                """
                INSERT INTO hotel_platform_accounts (
                    hotel_id,
                    platform_id,
                    external_account_id,
                    display_name,
                    account_status,
                    sync_enabled,
                    config,
                    raw_payload
                )
                VALUES (
                    CAST(:hotel_id AS uuid),
                    CAST(:platform_id AS uuid),
                    :external_account_id,
                    :display_name,
                    'active',
                    TRUE,
                    CAST(:config AS jsonb),
                    CAST(:raw_payload AS jsonb)
                )
                ON CONFLICT (hotel_id, platform_id, external_account_id)
                DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    account_status = 'active',
                    sync_enabled = TRUE,
                    config = EXCLUDED.config,
                    raw_payload = EXCLUDED.raw_payload,
                    updated_at = NOW()
                RETURNING id::text AS id
                """
            ),
            {
                "hotel_id": hotel_id,
                "platform_id": platform_id,
                "external_account_id": external_account_id,
                "display_name": display_name,
                "config": to_jsonb_param(config),
                "raw_payload": to_jsonb_param(raw_payload),
            },
        )
        return dict(result.mappings().one())

    def delete_hotel_platform_accounts(self, *, hotel_id: str) -> int:
        result = self.db.execute(
            text(
                """
                DELETE FROM hotel_platform_accounts
                WHERE hotel_id = CAST(:hotel_id AS uuid)
                RETURNING id
                """
            ),
            {"hotel_id": hotel_id},
        )
        return len(result.fetchall())

    def update_hotel(
        self,
        *,
        hotel_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        result = self.db.execute(
            text(
                """
                UPDATE hotels
                SET
                    hotel_code = :hotel_code,
                    hotel_name = :hotel_name,
                    legal_name = :legal_name,
                    timezone = :timezone,
                    country_code = :country_code,
                    city = :city,
                    address_line1 = :address_line1,
                    address_line2 = :address_line2,
                    postal_code = :postal_code,
                    phone = :phone,
                    email = :email,
                    status = :status,
                    metadata = CAST(:metadata AS jsonb),
                    updated_at = NOW()
                WHERE id = CAST(:hotel_id AS uuid)
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
                "hotel_id": hotel_id,
                **payload,
                "metadata": to_jsonb_param(payload.get("metadata")),
            },
        )
        row = result.mappings().first()
        return dict(row) if row else None

    def delete_hotel(self, *, hotel_id: str) -> bool:
        result = self.db.execute(
            text(
                """
                DELETE FROM hotels
                WHERE id = CAST(:hotel_id AS uuid)
                RETURNING id
                """
            ),
            {"hotel_id": hotel_id},
        )
        return result.first() is not None

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
