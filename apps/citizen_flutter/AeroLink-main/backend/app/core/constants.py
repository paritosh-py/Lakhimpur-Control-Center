from enum import Enum

API_V1_PREFIX = "/api/v1"

HEALTH_STATUS_HEALTHY = "healthy"
HEALTH_STATUS_UNHEALTHY = "unhealthy"

ENVIRONMENT_DEVELOPMENT = "development"
ENVIRONMENT_PRODUCTION = "production"


class NodeType(str, Enum):
    """
    Supported AeroLink node types.
    """

    GATEWAY = "gateway"
    RELAY = "relay"
    SENSOR = "sensor"
    EMERGENCY_NODE = "emergency_node"


class NodeStatus(str, Enum):
    """
    Possible operational states of an AeroLink node.
    """

    ONLINE = "online"
    OFFLINE = "offline"
    INACTIVE = "inactive"


class IncidentType(str, Enum):
    """
    Supported AeroLink incident types.
    """

    MEDICAL = "medical"
    FIRE = "fire"
    ACCIDENT = "accident"
    NATURAL_HAZARD = "natural_hazard"
    SECURITY = "security"
    OTHER = "other"


class IncidentSeverity(str, Enum):
    """
    Severity levels for AeroLink incidents.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """
    Lifecycle states of an AeroLink incident.
    """

    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class PriorityLevel(str, Enum):
    """
    Priority levels calculated by the AeroLink Priority Engine.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """
    Lifecycle states of an AeroLink alert.
    """

    GENERATED = "generated"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
