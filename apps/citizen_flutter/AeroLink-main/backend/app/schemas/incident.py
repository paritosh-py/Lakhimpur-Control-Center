from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
from app.schemas.node import LocationSchema


class IncidentCreate(BaseModel):
    """
    Schema used when reporting a new AeroLink incident.
    """

    incident_type: IncidentType

    severity: IncidentSeverity

    description: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Description of the reported incident.",
    )

    location: LocationSchema

    reporting_node_id: str | None = Field(
        default=None,
        max_length=100,
        description="Optional node that reported the incident.",
    )


class IncidentStatusUpdate(BaseModel):
    """
    Schema used to update an incident's lifecycle status.
    """

    status: IncidentStatus


class IncidentResponse(BaseModel):
    """
    Schema returned when retrieving AeroLink incident information.
    """

    incident_id: str

    incident_type: IncidentType
    severity: IncidentSeverity
    description: str

    location: LocationSchema

    reporting_node_id: str | None

    status: IncidentStatus

    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
