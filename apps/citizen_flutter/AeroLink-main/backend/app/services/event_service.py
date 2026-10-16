from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect


class EventService:
    """
    Manages AeroLink real-time WebSocket connections
    and event broadcasting.
    """

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(
        self,
        websocket: WebSocket,
    ) -> None:
        """
        Accepts and registers a WebSocket connection.
        """

        await websocket.accept()

        self._connections.append(websocket)

    def disconnect(
        self,
        websocket: WebSocket,
    ) -> None:
        """
        Removes a disconnected WebSocket.
        """

        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(
        self,
        event: str,
        data: dict[str, object],
    ) -> None:
        """
        Broadcasts an event to all connected clients.
        """

        message: dict[str, object] = {
            "event": event,
            "data": data,
        }

        disconnected_connections: list[WebSocket] = []

        for websocket in self._connections:
            try:
                await websocket.send_json(message)

            except WebSocketDisconnect:
                disconnected_connections.append(websocket)

        for websocket in disconnected_connections:
            self.disconnect(websocket)


event_service = EventService()
