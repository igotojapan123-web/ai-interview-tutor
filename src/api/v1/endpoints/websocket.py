"""
WebSocket API Endpoints.

Handles WebSocket connections for real-time features.
"""

import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.security import HTTPBearer

from src.realtime.websocket import ws_manager
from src.realtime.events import Event, EventType
from src.services.auth_service import AuthService
from src.infrastructure.container import get_auth_service

logger = logging.getLogger(__name__)
router = APIRouter()

security = HTTPBearer(auto_error=False)


async def get_user_from_token(token: str) -> Optional[str]:
    """Extract user ID from JWT token."""
    try:
        auth_service = get_auth_service()
        user = auth_service.verify_access_token(token)
        return user.id
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    Main WebSocket endpoint.

    Connect with: ws://host/api/v1/ws?token=<jwt_token>

    Message Types:
    - join_room: {"type": "join_room", "room_id": "room-123"}
    - leave_room: {"type": "leave_room", "room_id": "room-123"}
    - chat_message: {"type": "chat_message", "room_id": "room-123", "content": "Hello"}
    - typing: {"type": "typing", "room_id": "room-123", "is_typing": true}
    """
    # Authenticate
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    user_id = await get_user_from_token(token)
    if not user_id:
        await websocket.close(code=4002, reason="Invalid token")
        return

    # Handle connection
    await ws_manager.handle_connection(websocket, user_id)


@router.websocket("/ws/chat/{room_id}")
async def chat_websocket(
    websocket: WebSocket,
    room_id: str,
    token: Optional[str] = Query(None)
):
    """
    Chat room WebSocket endpoint.

    Automatically joins the specified room.

    Connect with: ws://host/api/v1/ws/chat/room-123?token=<jwt_token>
    """
    # Authenticate
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    user_id = await get_user_from_token(token)
    if not user_id:
        await websocket.close(code=4002, reason="Invalid token")
        return

    # Connect and join room
    connection = await ws_manager.connection_manager.connect(websocket, user_id)
    await ws_manager.connection_manager.join_room(connection, room_id)

    try:
        while True:
            data = await websocket.receive_json()

            # Handle chat-specific messages
            message_type = data.get("type")

            if message_type == "chat_message":
                from src.realtime.events import create_chat_message_event
                event = create_chat_message_event(
                    room_id=room_id,
                    sender_id=user_id,
                    sender_name=data.get("sender_name", "Unknown"),
                    content=data.get("content", "")
                )
                await ws_manager.connection_manager.send_to_room(
                    room_id,
                    event,
                    exclude={user_id}
                )

                # Echo back to sender
                await ws_manager.connection_manager.send_to_connection(connection, event)

            elif message_type == "typing":
                from src.realtime.events import TypingIndicator
                event = Event(
                    type=EventType.CHAT_TYPING,
                    room_id=room_id,
                    data={
                        "user_id": user_id,
                        "user_name": data.get("user_name", "Unknown"),
                        "is_typing": data.get("is_typing", True)
                    }
                )
                await ws_manager.connection_manager.send_to_room(
                    room_id,
                    event,
                    exclude={user_id}
                )

    except WebSocketDisconnect:
        await ws_manager.connection_manager.disconnect(connection)


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return ws_manager.connection_manager.get_stats()


@router.get("/ws/online/{user_id}")
async def check_user_online(user_id: str):
    """Check if a user is online."""
    return {"user_id": user_id, "online": ws_manager.connection_manager.is_user_online(user_id)}
