"""
WebSocket Connection Management.

Handles WebSocket connections, rooms, and message broadcasting.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, List, Any
from dataclasses import dataclass, field

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from src.realtime.events import Event, EventType

logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """Represents a WebSocket connection."""

    websocket: WebSocket
    user_id: str
    connected_at: datetime = field(default_factory=datetime.utcnow)
    rooms: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Check if connection is still active."""
        return self.websocket.client_state == WebSocketState.CONNECTED


class ConnectionManager:
    """
    Manages WebSocket connections.

    Handles user connections, room subscriptions, and message routing.
    """

    def __init__(self):
        # user_id -> Set[Connection] (one user can have multiple connections)
        self._connections: Dict[str, Set[Connection]] = {}

        # room_id -> Set[user_id]
        self._rooms: Dict[str, Set[str]] = {}

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        metadata: Dict[str, Any] = None
    ) -> Connection:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket instance
            user_id: User identifier
            metadata: Optional connection metadata

        Returns:
            Connection object
        """
        await websocket.accept()

        connection = Connection(
            websocket=websocket,
            user_id=user_id,
            metadata=metadata or {}
        )

        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(connection)

        logger.info(f"User {user_id} connected. Total connections: {self.total_connections}")

        # Send connected event
        await self.send_to_connection(connection, Event(
            type=EventType.CONNECTED,
            user_id=user_id,
            data={"message": "Connected to FlyReady Lab"}
        ))

        return connection

    async def disconnect(self, connection: Connection) -> None:
        """
        Disconnect and clean up a connection.

        Args:
            connection: Connection to disconnect
        """
        user_id = connection.user_id

        async with self._lock:
            # Remove from user connections
            if user_id in self._connections:
                self._connections[user_id].discard(connection)
                if not self._connections[user_id]:
                    del self._connections[user_id]

            # Remove from all rooms
            for room_id in list(connection.rooms):
                await self._leave_room(connection, room_id)

        logger.info(f"User {user_id} disconnected. Total connections: {self.total_connections}")

    async def join_room(self, connection: Connection, room_id: str) -> None:
        """
        Add connection to a room.

        Args:
            connection: Connection to add
            room_id: Room identifier
        """
        async with self._lock:
            if room_id not in self._rooms:
                self._rooms[room_id] = set()
            self._rooms[room_id].add(connection.user_id)
            connection.rooms.add(room_id)

        logger.debug(f"User {connection.user_id} joined room {room_id}")

    async def leave_room(self, connection: Connection, room_id: str) -> None:
        """
        Remove connection from a room.

        Args:
            connection: Connection to remove
            room_id: Room identifier
        """
        async with self._lock:
            await self._leave_room(connection, room_id)

    async def _leave_room(self, connection: Connection, room_id: str) -> None:
        """Internal room leave (assumes lock is held)."""
        if room_id in self._rooms:
            self._rooms[room_id].discard(connection.user_id)
            if not self._rooms[room_id]:
                del self._rooms[room_id]
        connection.rooms.discard(room_id)

    async def send_to_connection(self, connection: Connection, event: Event) -> bool:
        """
        Send event to a specific connection.

        Args:
            connection: Target connection
            event: Event to send

        Returns:
            True if sent successfully
        """
        try:
            if connection.is_active:
                await connection.websocket.send_json(event.model_dump())
                return True
        except Exception as e:
            logger.error(f"Failed to send to connection: {e}")
        return False

    async def send_to_user(self, user_id: str, event: Event) -> int:
        """
        Send event to all connections of a user.

        Args:
            user_id: Target user
            event: Event to send

        Returns:
            Number of connections sent to
        """
        sent_count = 0
        connections = self._connections.get(user_id, set())

        for connection in list(connections):
            if await self.send_to_connection(connection, event):
                sent_count += 1

        return sent_count

    async def send_to_room(self, room_id: str, event: Event, exclude: Set[str] = None) -> int:
        """
        Send event to all users in a room.

        Args:
            room_id: Target room
            event: Event to send
            exclude: User IDs to exclude

        Returns:
            Number of users sent to
        """
        exclude = exclude or set()
        sent_count = 0

        user_ids = self._rooms.get(room_id, set())

        for user_id in user_ids:
            if user_id not in exclude:
                sent_count += await self.send_to_user(user_id, event)

        return sent_count

    async def broadcast(self, event: Event, exclude: Set[str] = None) -> int:
        """
        Broadcast event to all connected users.

        Args:
            event: Event to broadcast
            exclude: User IDs to exclude

        Returns:
            Number of users sent to
        """
        exclude = exclude or set()
        sent_count = 0

        for user_id in list(self._connections.keys()):
            if user_id not in exclude:
                sent_count += await self.send_to_user(user_id, event)

        return sent_count

    def get_user_connections(self, user_id: str) -> List[Connection]:
        """Get all connections for a user."""
        return list(self._connections.get(user_id, []))

    def get_room_users(self, room_id: str) -> Set[str]:
        """Get all users in a room."""
        return self._rooms.get(room_id, set()).copy()

    def is_user_online(self, user_id: str) -> bool:
        """Check if user has any active connections."""
        return user_id in self._connections and bool(self._connections[user_id])

    @property
    def total_connections(self) -> int:
        """Total number of active connections."""
        return sum(len(conns) for conns in self._connections.values())

    @property
    def online_users(self) -> int:
        """Number of online users."""
        return len(self._connections)

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": self.total_connections,
            "online_users": self.online_users,
            "active_rooms": len(self._rooms),
            "room_stats": {
                room_id: len(users)
                for room_id, users in self._rooms.items()
            }
        }


class WebSocketManager:
    """
    High-level WebSocket manager.

    Provides a simplified interface for WebSocket operations.
    """

    _instance: Optional["WebSocketManager"] = None

    def __init__(self):
        self.connection_manager = ConnectionManager()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = 30  # seconds

    @classmethod
    def get_instance(cls) -> "WebSocketManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(self) -> None:
        """Start the WebSocket manager."""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            logger.info("WebSocket manager started")

    async def stop(self) -> None:
        """Stop the WebSocket manager."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
            logger.info("WebSocket manager stopped")

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat to all connections."""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)

                heartbeat = Event(
                    type=EventType.HEARTBEAT,
                    broadcast=True,
                    data={"timestamp": datetime.utcnow().isoformat()}
                )

                await self.connection_manager.broadcast(heartbeat)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: str
    ) -> None:
        """
        Handle a WebSocket connection lifecycle.

        Args:
            websocket: WebSocket instance
            user_id: User identifier
        """
        connection = await self.connection_manager.connect(websocket, user_id)

        try:
            while True:
                # Receive and process messages
                data = await websocket.receive_json()
                await self._handle_message(connection, data)

        except WebSocketDisconnect:
            await self.connection_manager.disconnect(connection)
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            await self.connection_manager.disconnect(connection)

    async def _handle_message(self, connection: Connection, data: Dict[str, Any]) -> None:
        """
        Handle incoming WebSocket message.

        Args:
            connection: Source connection
            data: Message data
        """
        message_type = data.get("type")

        if message_type == "join_room":
            room_id = data.get("room_id")
            if room_id:
                await self.connection_manager.join_room(connection, room_id)

        elif message_type == "leave_room":
            room_id = data.get("room_id")
            if room_id:
                await self.connection_manager.leave_room(connection, room_id)

        elif message_type == "chat_message":
            room_id = data.get("room_id")
            content = data.get("content")
            if room_id and content:
                from src.realtime.events import create_chat_message_event
                event = create_chat_message_event(
                    room_id=room_id,
                    sender_id=connection.user_id,
                    sender_name=data.get("sender_name", "Unknown"),
                    content=content
                )
                await self.connection_manager.send_to_room(
                    room_id,
                    event,
                    exclude={connection.user_id}
                )

        elif message_type == "typing":
            room_id = data.get("room_id")
            if room_id:
                from src.realtime.events import TypingIndicator
                indicator = TypingIndicator(
                    room_id=room_id,
                    user_id=connection.user_id,
                    user_name=data.get("user_name", "Unknown"),
                    is_typing=data.get("is_typing", True)
                )
                event = Event(
                    type=EventType.CHAT_TYPING,
                    room_id=room_id,
                    data=indicator.model_dump()
                )
                await self.connection_manager.send_to_room(
                    room_id,
                    event,
                    exclude={connection.user_id}
                )

    # Convenience methods
    async def notify_user(self, user_id: str, event: Event) -> int:
        """Send notification to user."""
        return await self.connection_manager.send_to_user(user_id, event)

    async def notify_room(self, room_id: str, event: Event) -> int:
        """Send notification to room."""
        return await self.connection_manager.send_to_room(room_id, event)

    async def broadcast(self, event: Event) -> int:
        """Broadcast to all users."""
        return await self.connection_manager.broadcast(event)


# Global instance
ws_manager = WebSocketManager.get_instance()
