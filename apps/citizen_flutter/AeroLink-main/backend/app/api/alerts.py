from fastapi import APIRouter, HTTPException, status

from app.schemas.alert import (
    AlertResponse,
    AlertStatusUpdate,
)
from app.services.alert_service import alert_service
from app.services.event_service import event_service

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


@router.post(
    "/{incident_id}/generate",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_alert(
    incident_id: str,
) -> AlertResponse:
    """
    Generates an AeroLink alert for an existing incident.
    """

    try:
        alert_document = alert_service.generate_alert(incident_id)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    response = AlertResponse.model_validate(alert_document)

    await event_service.broadcast(
        event="alert.generated",
        data={
            "alert_id": response.alert_id,
            "incident_id": response.incident_id,
            "priority_level": (response.priority_level.value),
            "priority_score": response.priority_score,
            "status": response.status.value,
        },
    )

    return response


@router.get(
    "/",
    response_model=list[AlertResponse],
)
def get_all_alerts() -> list[AlertResponse]:
    """
    Retrieves all AeroLink alerts.
    """

    alert_documents = alert_service.get_all_alerts()

    return [
        AlertResponse.model_validate(alert_document)
        for alert_document in alert_documents
    ]


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
)
def get_alert(
    alert_id: str,
) -> AlertResponse:
    """
    Retrieves a specific AeroLink alert.
    """

    alert_document = alert_service.get_alert(alert_id)

    if alert_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' was not found.",
        )

    return AlertResponse.model_validate(alert_document)


@router.patch(
    "/{alert_id}/status",
    response_model=AlertResponse,
)
async def update_alert_status(
    alert_id: str,
    status_update: AlertStatusUpdate,
) -> AlertResponse:
    """
    Updates an AeroLink alert lifecycle status.
    """

    alert_document = alert_service.update_status(
        alert_id,
        status_update.status,
    )

    if alert_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' was not found.",
        )

    response = AlertResponse.model_validate(alert_document)

    await event_service.broadcast(
        event="alert.updated",
        data={
            "alert_id": response.alert_id,
            "incident_id": response.incident_id,
            "status": response.status.value,
            "priority_level": (response.priority_level.value),
        },
    )

    return response
