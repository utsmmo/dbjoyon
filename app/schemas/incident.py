from pydantic import BaseModel

from app.schemas.common import IncidentSummary


class IncidentListResponse(BaseModel):
    items: list[IncidentSummary]
    total: int
    limit: int
    offset: int
