from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.hotel_repository import HotelRepository
from app.schemas.hotel import HotelCreateRequest, HotelListResponse, HotelResponse


class HotelService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.hotel_repository = HotelRepository(db)

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
