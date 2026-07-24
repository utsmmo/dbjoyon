from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.hotel import HotelCreateRequest, HotelListResponse, HotelResponse
from app.services.hotel_service import HotelService

router = APIRouter(tags=["hotels"])


@router.post("/hotels", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
def create_hotel(
    payload: HotelCreateRequest,
    db: Session = Depends(db_session),
) -> HotelResponse:
    service = HotelService(db)
    try:
        return service.create_hotel(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/hotels", response_model=HotelListResponse)
def list_hotels(
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_session),
) -> HotelListResponse:
    service = HotelService(db)
    return service.list_hotels(q=q, status=status, limit=limit, offset=offset)
