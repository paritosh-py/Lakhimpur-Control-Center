from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.network import (
    IncidentNetworkContextResponse,
    NearbyNodeResponse,
    NetworkOverviewResponse,
)
from app.schemas.node import LocationSchema
from app.services.spatial_service import spatial_service

router = APIRouter(
    prefix="/network",
    tags=["Network Intelligence"],
)


@router.get(
    "/overview",
    response_model=NetworkOverviewResponse,
)
def get_network_overview() -> NetworkOverviewResponse:
    """
    Retrieves a summary of the AeroLink network.
    """

    overview = spatial_service.get_network_overview()

    return NetworkOverviewResponse.model_validate(overview)


@router.get(
    "/nodes/nearby",
    response_model=list[NearbyNodeResponse],
)
def get_nearby_nodes(
    latitude: Annotated[float, Query()],
    longitude: Annotated[float, Query()],
    radius_meters: Annotated[
        float,
        Query(gt=0),
    ] = 5_000,
) -> list[NearbyNodeResponse]:
    """
    Retrieves AeroLink nodes near a geographic location.
    """

    nearby_nodes = spatial_service.get_nearby_nodes(
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
    )

    return [
        NearbyNodeResponse(
            node_id=node["node_id"],
            distance_meters=round(distance, 2),
            status=node["status"],
        )
        for node, distance in nearby_nodes
    ]


@router.get(
    "/incidents/{incident_id}/context",
    response_model=IncidentNetworkContextResponse,
)
def get_incident_network_context(
    incident_id: str,
    radius_meters: Annotated[
        float,
        Query(gt=0),
    ] = 5_000,
) -> IncidentNetworkContextResponse:
    """
    Retrieves spatial and network context around an incident.
    """

    context = spatial_service.get_incident_network_context(
        incident_id=incident_id,
        radius_meters=radius_meters,
    )

    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' was not found.",
        )

    (
        incident,
        nearby_nodes,
        nearest_online_node,
        network_risk,
    ) = context

    nearest_online_response: NearbyNodeResponse | None = None

    if nearest_online_node is not None:
        node, distance = nearest_online_node

        nearest_online_response = NearbyNodeResponse(
            node_id=node["node_id"],
            distance_meters=round(distance, 2),
            status=node["status"],
        )

    nearby_node_responses = [
        NearbyNodeResponse(
            node_id=node["node_id"],
            distance_meters=round(distance, 2),
            status=node["status"],
        )
        for node, distance in nearby_nodes
    ]

    return IncidentNetworkContextResponse(
        incident_id=incident["incident_id"],
        location=LocationSchema(
            latitude=incident["location"]["latitude"],
            longitude=incident["location"]["longitude"],
        ),
        nearest_online_node=nearest_online_response,
        nearby_nodes=nearby_node_responses,
        network_risk=network_risk,
    )
