from fastapi import APIRouter, HTTPException, status

from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentStatusUpdate,
)
from app.services.event_service import event_service
from app.services.incident_service import incident_service

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


@router.post(
    "/",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_incident(
    incident: IncidentCreate,
) -> IncidentResponse:
    """
    Creates a new AeroLink incident.
    """

    incident_document = incident_service.create_incident(incident)

    response = IncidentResponse.model_validate(incident_document)

    await event_service.broadcast(
        event="incident.created",
        data={
            "incident_id": response.incident_id,
            "incident_type": response.incident_type.value,
            "status": response.status.value,
        },
    )

    return response


@router.get(
    "/",
    response_model=list[IncidentResponse],
)
def get_all_incidents() -> list[IncidentResponse]:
    """
    Retrieves all AeroLink incidents.
    """

    incident_documents = incident_service.get_all_incidents()

    return [
        IncidentResponse.model_validate(incident_document)
        for incident_document in incident_documents
    ]


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
)
def get_incident(
    incident_id: str,
) -> IncidentResponse:
    """
    Retrieves a specific AeroLink incident.
    """

    incident_document = incident_service.get_incident(incident_id)

    if incident_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' was not found.",
        )

    return IncidentResponse.model_validate(incident_document)


@router.patch(
    "/{incident_id}/status",
    response_model=IncidentResponse,
)
async def update_incident_status(
    incident_id: str,
    status_update: IncidentStatusUpdate,
) -> IncidentResponse:
    """
    Updates the lifecycle status of an AeroLink incident.
    """

    incident_document = incident_service.update_status(
        incident_id,
        status_update,
    )

    if incident_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' was not found.",
        )

    response = IncidentResponse.model_validate(incident_document)

    await event_service.broadcast(
        event="incident.updated",
        data={
            "incident_id": response.incident_id,
            "status": response.status.value,
        },
    )

    return response
