from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import NodeStatus, NodeType


class LocationSchema(BaseModel):
    """
    Geographic location of an AeroLink node.
    """

    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Latitude of the node.",
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Longitude of the node.",
    )


class NodeCreate(BaseModel):
    """
    Schema used when registering a new AeroLink node.
    """

    node_id: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Unique AeroLink node identifier.",
    )

    node_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Human-readable node name.",
    )

    node_type: NodeType

    location: LocationSchema


class NodeTelemetry(BaseModel):
    """
    Live telemetry received from an AeroLink node.
    """

    battery_level: int = Field(
        ...,
        ge=0,
        le=100,
        description="Current battery percentage.",
    )

    signal_strength: int = Field(
        ...,
        description="Current signal strength in dBm.",
    )

    status: NodeStatus


class NodeResponse(BaseModel):
    """
    Schema returned when retrieving AeroLink node information.
    """

    node_id: str
    node_name: str
    node_type: NodeType

    location: LocationSchema

    status: NodeStatus
    battery_level: int | None
    signal_strength: int | None

    last_seen: datetime | None
    created_at: datetime
