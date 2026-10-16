from fastapi import APIRouter, HTTPException, status

from app.schemas.node import NodeCreate, NodeResponse, NodeTelemetry
from app.services.event_service import event_service
from app.services.node_service import node_service

router = APIRouter(
    prefix="/nodes",
    tags=["Nodes"],
)


@router.post(
    "/",
    response_model=NodeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_node(
    node: NodeCreate,
) -> NodeResponse:
    """
    Registers a new AeroLink node.
    """

    try:
        node_document = node_service.register_node(node)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    response = NodeResponse.model_validate(node_document)

    await event_service.broadcast(
        event="node.registered",
        data={
            "node_id": response.node_id,
            "status": response.status.value,
        },
    )

    return response


@router.get(
    "/",
    response_model=list[NodeResponse],
)
def get_all_nodes() -> list[NodeResponse]:
    """
    Retrieves all registered AeroLink nodes.
    """

    node_documents = node_service.get_all_nodes()

    return [
        NodeResponse.model_validate(node_document) for node_document in node_documents
    ]


@router.get(
    "/{node_id}",
    response_model=NodeResponse,
)
def get_node(node_id: str) -> NodeResponse:
    """
    Retrieves a specific AeroLink node.
    """

    node_document = node_service.get_node(node_id)

    if node_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{node_id}' was not found.",
        )

    return NodeResponse.model_validate(node_document)


@router.post(
    "/{node_id}/telemetry",
    response_model=NodeResponse,
)
async def update_node_telemetry(
    node_id: str,
    telemetry: NodeTelemetry,
) -> NodeResponse:
    """
    Updates the latest telemetry received from an AeroLink node.
    """

    node_document = node_service.update_telemetry(
        node_id,
        telemetry,
    )

    if node_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{node_id}' was not found.",
        )

    response = NodeResponse.model_validate(node_document)

    await event_service.broadcast(
        event="node.updated",
        data={
            "node_id": response.node_id,
            "status": response.status.value,
            "signal_strength": response.signal_strength,
        },
    )

    return response
