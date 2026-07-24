from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.incident import IncidentListResponse
from app.services.incident_query_service import IncidentQueryService

router = APIRouter(tags=["incidents"])


@router.get("/incidents", response_model=IncidentListResponse)
def list_incidents(
    hotel_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_session),
) -> IncidentListResponse:
    service = IncidentQueryService(db)
    return service.list_incidents(
        hotel_id=hotel_id,
        status=status,
        severity=severity,
        limit=limit,
        offset=offset,
    )
