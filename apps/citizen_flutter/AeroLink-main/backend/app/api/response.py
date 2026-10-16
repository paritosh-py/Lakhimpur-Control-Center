from fastapi import APIRouter, HTTPException, status

from app.schemas.response import (
    IncidentResponseRecommendation,
    NetworkResponse,
    PriorityResponse,
    RecommendationResponse,
)
from app.services.response_service import response_service

router = APIRouter(
    prefix="/response",
    tags=["Response Engine"],
)


@router.get(
    "/incidents/{incident_id}/recommendation",
    response_model=IncidentResponseRecommendation,
)
def get_incident_response_recommendation(
    incident_id: str,
) -> IncidentResponseRecommendation:
    """
    Retrieves a complete response recommendation for an incident.
    """

    response_data = response_service.get_incident_response(incident_id)

    if response_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(f"Incident or generated alert for '{incident_id}' was not found."),
        )

    (
        incident,
        alert,
        network_risk,
        nearest_online_node_id,
        action,
        urgency,
        communication_strategy,
    ) = response_data

    return IncidentResponseRecommendation(
        incident_id=incident["incident_id"],
        priority=PriorityResponse(
            score=alert["priority_score"],
            level=alert["priority_level"],
        ),
        network=NetworkResponse(
            risk=network_risk,
            nearest_online_node_id=nearest_online_node_id,
        ),
        recommendation=RecommendationResponse(
            action=action,
            urgency=urgency,
            communication_strategy=communication_strategy,
        ),
    )
