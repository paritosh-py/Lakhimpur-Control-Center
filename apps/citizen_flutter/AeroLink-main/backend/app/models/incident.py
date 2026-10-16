from datetime import datetime
from typing import TypedDict

from app.core.constants import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
from app.models.node import LocationDocument


class IncidentDocument(TypedDict):
    """
    MongoDB representation of an AeroLink incident.
    """

    incident_id: str

    incident_type: IncidentType
    severity: IncidentSeverity
    description: str

    location: LocationDocument

    reporting_node_id: str | None

    status: IncidentStatus

    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
