import json
import logging
from typing import Any, Dict

from fastapi import WebSocket, WebSocketDisconnect

from app.shared.security.jwt import decode_token

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[
            str, list[WebSocket]
        ] = {}

    async def connect(
        self, websocket: WebSocket, user_id: str
    ):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(
            f"WebSocket connected: user={user_id}"
        )

    def disconnect(
        self, websocket: WebSocket, user_id: str
    ):
        if user_id in self.active_connections:
            if (
                websocket
                in self.active_connections[user_id]
            ):
                self.active_connections[user_id].remove(
                    websocket
                )
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(
            f"WebSocket disconnected: user={user_id}"
        )

    async def send_to_user(
        self, user_id: str, message: dict
    ):
        if user_id in self.active_connections:
            for connection in self.active_connections[
                user_id
            ]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def broadcast(self, message: dict):
        for user_id in self.active_connections:
            await self.send_to_user(user_id, message)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    user_id = None
    try:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(
                code=4001, reason="No token provided"
            )
            return

        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(
                code=4001, reason="Invalid token"
            )
            return

        await manager.connect(websocket, user_id)

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type", "")

            if message_type == "chat":
                await _handle_chat_message(
                    websocket, user_id, message
                )
            elif message_type == "ping":
                await websocket.send_json(
                    {"type": "pong"}
                )

    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if user_id:
            manager.disconnect(websocket, user_id)


async def _handle_chat_message(
    websocket: WebSocket,
    user_id: str,
    message: dict,
):
    try:
        from app.modules.chat.service import ChatService

        chat_service = ChatService()

        from app.modules.chat.schema import (
            SendMessageRequest,
        )

        request = SendMessageRequest(
            session_id=message.get("session_id"),
            message=message.get("content", ""),
        )

        from app.database.models.user import User

        user = await User.get(user_id)
        if not user:
            await websocket.send_json(
                {
                    "type": "error",
                    "content": "User not found",
                }
            )
            return

        async for chunk in chat_service.send_message(
            user, request
        ):
            await websocket.send_json(chunk)

    except Exception as e:
        logger.error(
            f"Chat message handling error: {e}"
        )
        await websocket.send_json(
            {
                "type": "error",
                "content": "Failed to process message",
            }
        )
