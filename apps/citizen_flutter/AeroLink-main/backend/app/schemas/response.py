from pydantic import BaseModel

from app.core.constants import PriorityLevel


class PriorityResponse(BaseModel):
    """
    Priority information used by the response engine.
    """

    score: int
    level: PriorityLevel


class NetworkResponse(BaseModel):
    """
    Network information relevant to incident response.
    """

    risk: str
    nearest_online_node_id: str | None


class RecommendationResponse(BaseModel):
    """
    Action recommended by the AeroLink Response Engine.
    """

    action: str
    urgency: str
    communication_strategy: str


class IncidentResponseRecommendation(BaseModel):
    """
    Complete response recommendation for an AeroLink incident.
    """

    incident_id: str

    priority: PriorityResponse
    network: NetworkResponse
    recommendation: RecommendationResponse
