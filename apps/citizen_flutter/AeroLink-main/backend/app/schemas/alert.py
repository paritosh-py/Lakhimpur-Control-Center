from datetime import datetime

from pydantic import BaseModel

from app.core.constants import AlertStatus, PriorityLevel


class AlertStatusUpdate(BaseModel):
    """
    Schema used to update an AeroLink alert status.
    """

    status: AlertStatus


class AlertResponse(BaseModel):
    """
    Schema returned when retrieving AeroLink alert information.
    """

    alert_id: str
    incident_id: str

    priority_score: int
    priority_level: PriorityLevel

    severity_score: int
    incident_type_score: int
    network_score: int

    status: AlertStatus

    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
