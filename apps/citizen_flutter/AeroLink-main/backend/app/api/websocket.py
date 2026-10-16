from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from app.services.event_service import event_service

router = APIRouter(
    prefix="/ws",
    tags=["Real-Time Events"],
)


@router.websocket("/events")
async def websocket_events(
    websocket: WebSocket,
) -> None:
    """
    Maintains a live connection with an AeroLink client.
    """

    await event_service.connect(websocket)

    try:
        while True:
            _ = await websocket.receive_text()

    except WebSocketDisconnect:
        event_service.disconnect(websocket)


@router.post("/test-event")
async def send_test_event() -> dict[str, str]:
    """
    Broadcasts a test event to all connected clients.
    """

    await event_service.broadcast(
        event="system.test",
        data={
            "message": "AeroLink real-time events are working.",
        },
    )

    return {
        "status": "broadcast_sent",
    }
