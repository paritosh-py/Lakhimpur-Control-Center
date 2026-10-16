from datetime import datetime
from typing import TypedDict

from app.core.constants import AlertStatus, PriorityLevel


class AlertDocument(TypedDict):
    """
    MongoDB representation of an AeroLink alert.
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
