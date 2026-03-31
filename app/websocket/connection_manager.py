from typing import Dict, Optional, Any
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        # room_name -> { session_id: {"ws": WebSocket, "user_id": int, "username": str} }
        self.active_rooms: Dict[str, Dict[str, dict]] = {}

    async def connect(self, websocket: WebSocket, room_name: str, user_id: int, username: str) -> str:
        """Подключить пользователя к комнате"""
        await websocket.accept()

        # Генерируем уникальный session_id
        import uuid
        session_id = str(uuid.uuid4())

        if room_name not in self.active_rooms:
            self.active_rooms[room_name] = {}

        self.active_rooms[room_name][session_id] = {
            "ws": websocket,
            "user_id": user_id,
            "username": username
        }

        return session_id

    def disconnect(self, room_name: str, session_id: str):
        """Отключить пользователя от комнаты"""
        if room_name in self.active_rooms and session_id in self.active_rooms[room_name]:
            del self.active_rooms[room_name][session_id]

            if len(self.active_rooms[room_name]) == 0:
                del self.active_rooms[room_name]

    async def send_to_user(self, room_name: str, target_session_id: str, message: dict):
        """Отправить сообщение конкретному пользователю"""
        if (room_name in self.active_rooms and
                target_session_id in self.active_rooms[room_name]):
            try:
                await self.active_rooms[room_name][target_session_id]["ws"].send_json(message)
            except Exception as e:
                print(f"Error sending to user: {e}")

    async def broadcast_to_room(self, room_name: str, message: dict, exclude_session_id: str = None):
        """Отправить сообщение всем в комнате"""
        if room_name in self.active_rooms:
            for session_id, connection in self.active_rooms[room_name].items():
                if exclude_session_id is None or session_id != exclude_session_id:
                    try:
                        await connection["ws"].send_json(message)
                    except Exception as e:
                        print(f"Error broadcasting: {e}")

    def get_users_in_room(self, room_name: str) -> list:
        """Получить список пользователей в комнате"""
        if room_name in self.active_rooms:
            return [
                {
                    "session_id": sid,
                    "user_id": conn["user_id"],
                    "username": conn["username"]
                }
                for sid, conn in self.active_rooms[room_name].items()
            ]
        return []


manager = ConnectionManager()