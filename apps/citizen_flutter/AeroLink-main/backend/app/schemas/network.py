from pydantic import BaseModel

from app.core.constants import NodeStatus
from app.schemas.node import LocationSchema


class NearbyNodeResponse(BaseModel):
    """
    Represents a node returned from a spatial proximity query.
    """

    node_id: str
    distance_meters: float
    status: NodeStatus


class NetworkOverviewResponse(BaseModel):
    """
    Summarizes the current AeroLink network state.
    """

    total_nodes: int
    online_nodes: int
    offline_nodes: int
    inactive_nodes: int
    average_signal_strength: float | None


class IncidentNetworkContextResponse(BaseModel):
    """
    Represents network context around an incident.
    """

    incident_id: str
    location: LocationSchema
    nearest_online_node: NearbyNodeResponse | None
    nearby_nodes: list[NearbyNodeResponse]
    network_risk: str
