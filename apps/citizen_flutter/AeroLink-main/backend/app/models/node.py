from datetime import datetime
from typing import TypedDict

from app.core.constants import NodeStatus, NodeType


class LocationDocument(TypedDict):
    """
    MongoDB representation of a node location.
    """

    latitude: float
    longitude: float


class NodeDocument(TypedDict):
    """
    MongoDB representation of an AeroLink node.
    """

    node_id: str
    node_name: str
    node_type: NodeType

    location: LocationDocument

    status: NodeStatus
    battery_level: int | None
    signal_strength: int | None

    last_seen: datetime | None
    created_at: datetime
    updated_at: datetime
