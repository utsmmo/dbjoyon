import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.hotel_repository import HotelRepository
from app.repositories.platform_repository import PlatformRepository
from app.schemas.hotel_admin import (
    HotelAdminUpsertRequest,
    HotelDeleteResponse,
    HotelImportItem,
    HotelImportSummary,
    HotelPurgeResponse,
    HotelResetImportRequest,
    HotelResetImportResponse,
)
from app.schemas.hotel import HotelCreateRequest, HotelListResponse, HotelResponse
from app.services.link_normalizer import normalize_source_links


class HotelService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.hotel_repository = HotelRepository(db)
        self.platform_repository = PlatformRepository(db)

    def create_hotel(self, payload: HotelCreateRequest) -> HotelResponse:
        if payload.status not in {"active", "inactive"}:
            raise ValueError("status must be either 'active' or 'inactive'")

        try:
            hotel = self.hotel_repository.create_hotel(payload.model_dump(mode="json"))
            self.db.commit()
            return HotelResponse(**hotel)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError(
                f"hotel_code already exists or hotel data is invalid: {payload.hotel_code}"
            ) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError(
                f"database error while creating hotel: {payload.hotel_code}"
            ) from exc

    def list_hotels(
        self,
        *,
        q: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> HotelListResponse:
        items, total = self.hotel_repository.list_hotels(
            q=q,
            status=status,
            limit=limit,
            offset=offset,
        )
        return HotelListResponse(items=items, total=total, limit=limit, offset=offset)

    def purge_all_hotels(self, *, confirm_purge: bool) -> HotelPurgeResponse:
        if not confirm_purge:
            raise ValueError("confirm_purge must be true")

        try:
            deleted_hotels = self.hotel_repository.delete_all_hotels()
            self.db.commit()
            return HotelPurgeResponse(
                deleted_hotels=deleted_hotels,
                deleted_at=datetime.now().astimezone(),
                status="success",
            )
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while purging hotels") from exc

    def reset_and_import_hotels(
        self,
        payload: HotelResetImportRequest,
    ) -> HotelResetImportResponse:
        if not payload.confirm_purge:
            raise ValueError("confirm_purge must be true")
        if not payload.hotels:
            raise ValueError("hotels must not be empty")

        try:
            deleted_hotels, imported_items, imported_accounts = self._replace_hotels(
                payload.hotels
            )
            self.db.commit()
            return HotelResetImportResponse(
                deleted_hotels=deleted_hotels,
                imported_hotels=len(imported_items),
                imported_accounts=imported_accounts,
                items=imported_items,
                imported_at=datetime.now().astimezone(),
                status="success",
            )
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("hotel import payload contains duplicate or invalid data") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while resetting and importing hotels") from exc

    def reset_and_import_default_manifest(
        self,
        *,
        confirm_purge: bool,
    ) -> HotelResetImportResponse:
        if not confirm_purge:
            raise ValueError("confirm_purge must be true")

        manifest_path = Path(__file__).resolve().parents[2] / "ops" / "codex" / "raon_hotel_import_manifest.json"
        hotels_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        hotels = [HotelImportItem.model_validate(item) for item in hotels_data]
        return self.reset_and_import_hotels(
            HotelResetImportRequest(confirm_purge=True, hotels=hotels)
        )

    def create_admin_hotel(self, payload: HotelAdminUpsertRequest) -> HotelResponse:
        self._validate_status(payload.status)

        try:
            normalized_links = normalize_source_links(payload.links)
            hotel = self.hotel_repository.create_hotel(
                {
                    **payload.model_dump(mode="json", exclude={"links"}),
                    "metadata": self._build_hotel_metadata(payload.metadata, normalized_links),
                }
            )
            self._create_platform_accounts(
                hotel_id=str(hotel["id"]),
                hotel_name=payload.hotel_name,
                normalized_links=normalized_links,
            )
            self.db.commit()
            return HotelResponse(**hotel)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("hotel_code already exists or hotel data is invalid") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while creating admin hotel") from exc

    def update_admin_hotel(
        self,
        *,
        hotel_id: str,
        payload: HotelAdminUpsertRequest,
    ) -> HotelResponse:
        self._validate_status(payload.status)

        try:
            normalized_links = normalize_source_links(payload.links)
            hotel = self.hotel_repository.update_hotel(
                hotel_id=hotel_id,
                payload={
                    **payload.model_dump(mode="json", exclude={"links"}),
                    "metadata": self._build_hotel_metadata(payload.metadata, normalized_links),
                },
            )
            if hotel is None:
                raise ValueError("hotel not found")

            self.hotel_repository.delete_hotel_platform_accounts(hotel_id=hotel_id)
            self._create_platform_accounts(
                hotel_id=hotel_id,
                hotel_name=payload.hotel_name,
                normalized_links=normalized_links,
            )
            self.db.commit()
            return HotelResponse(**hotel)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("hotel update contains duplicate or invalid data") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while updating hotel") from exc

    def delete_admin_hotel(self, *, hotel_id: str) -> HotelDeleteResponse:
        try:
            deleted = self.hotel_repository.delete_hotel(hotel_id=hotel_id)
            if not deleted:
                raise ValueError("hotel not found")
            self.db.commit()
            return HotelDeleteResponse(
                deleted_hotel_id=hotel_id,
                deleted_at=datetime.now().astimezone(),
                status="success",
            )
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while deleting hotel") from exc

    def _create_platform_accounts(
        self,
        *,
        hotel_id: str,
        hotel_name: str,
        normalized_links: dict[str, list[str]],
    ) -> int:
        created = 0

        for platform_code, links in normalized_links.items():
            platform = self.platform_repository.get_platform_by_code(platform_code)
            if platform is None:
                continue

            canonical_link = links[0] if links else None
            for link in links:
                self.hotel_repository.create_hotel_platform_account(
                    hotel_id=hotel_id,
                    platform_id=str(platform["id"]),
                    external_account_id=link,
                    display_name=hotel_name,
                    config={
                        "source_link": link,
                        "canonical_link": canonical_link,
                        "platform_code": platform_code,
                    },
                    raw_payload={
                        "source_link": link,
                        "canonical_link": canonical_link,
                        "platform_code": platform_code,
                        "source_links": links,
                    },
                )
                created += 1

        return created

    def _replace_hotels(
        self,
        hotels: list[HotelImportItem],
    ) -> tuple[int, list[HotelImportSummary], int]:
        deleted_hotels = self.hotel_repository.delete_all_hotels()
        imported_items: list[HotelImportSummary] = []
        imported_accounts = 0

        for hotel_payload in hotels:
            normalized_links = normalize_source_links(hotel_payload.links)
            hotel = self.hotel_repository.create_hotel(
                {
                    **hotel_payload.model_dump(mode="json", exclude={"links"}),
                    "metadata": self._build_hotel_metadata(
                        hotel_payload.metadata,
                        normalized_links,
                    ),
                }
            )
            hotel_id = str(hotel["id"])
            accounts_created = self._create_platform_accounts(
                hotel_id=hotel_id,
                hotel_name=hotel_payload.hotel_name,
                normalized_links=normalized_links,
            )
            imported_accounts += accounts_created
            imported_items.append(
                HotelImportSummary(
                    hotel_id=hotel_id,
                    hotel_code=hotel_payload.hotel_code,
                    hotel_name=hotel_payload.hotel_name,
                    accounts_created=accounts_created,
                    normalized_links=normalized_links,
                )
            )

        return deleted_hotels, imported_items, imported_accounts

    def _build_hotel_metadata(
        self,
        metadata: dict[str, object],
        normalized_links: dict[str, list[str]],
    ) -> dict[str, object]:
        return {
            **metadata,
            "canonical_links": {
                platform_code: links[0]
                for platform_code, links in normalized_links.items()
                if links
            },
            "source_links": normalized_links,
            "link_rules_version": 1,
        }

    def _validate_status(self, status: str) -> None:
        if status not in {"active", "inactive"}:
            raise ValueError("status must be either 'active' or 'inactive'")
