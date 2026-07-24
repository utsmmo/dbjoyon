from sqlalchemy.orm import Session

from app.repositories.incident_repository import IncidentRepository
from app.schemas.incident import IncidentListResponse


class IncidentQueryService:
    def __init__(self, db: Session) -> None:
        self.incident_repository = IncidentRepository(db)

    def list_incidents(
        self,
        *,
        hotel_id: str | None,
        status: str | None,
        severity: str | None,
        limit: int,
        offset: int,
    ) -> IncidentListResponse:
        items, total = self.incident_repository.list_incidents(
            hotel_id=hotel_id,
            status=status,
            severity=severity,
            limit=limit,
            offset=offset,
        )
        return IncidentListResponse(items=items, total=total, limit=limit, offset=offset)
