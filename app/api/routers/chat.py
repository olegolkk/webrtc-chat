from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.websocket.connection_manager import manager
from app.api.dependencies.auth import get_user_from_token
from app.services.user_service import UserService, get_user_service
from app.services.message_service import MessageService, get_message_service
from app.services.room_service import RoomService, get_room_service
from app.db.base import get_db
import json
import asyncio

router = APIRouter(tags=["chat"])


@router.websocket("/ws/{room_name}")
async def websocket_endpoint(
        websocket: WebSocket,
        room_name: str,
        token: str = Query(...),
        db: AsyncSession = Depends(get_db)
):
    # Проверяем аутентификацию
    user_id = await get_user_from_token(websocket, token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Создаем сервисы (передаем db)
    user_service = UserService(db)
    room_service = RoomService(db)
    message_service = MessageService(db)

    try:
        # Получаем пользователя из БД
        user = await user_service.get_user_by_id(user_id)
        if not user:
            await websocket.close(code=4002, reason="User not found")
            return

        # Ищем или создаем комнату
        room = await room_service.get_room_by_name(room_name)
        if not room:
            from app.schemas.room import RoomCreate
            room = await room_service.create_room(
                RoomCreate(name=room_name, is_private=False),
                user_id
            )

        # Добавляем пользователя в комнату в БД
        await room_service.add_user_to_room(room.id, user_id)

        # Подключаем к WebSocket
        session_id = await manager.connect(websocket, room_name, user.id, user.username)

        # Получаем историю сообщений
        messages = await message_service.get_room_messages(room.id, limit=50)

        # Отправляем инициализацию
        await websocket.send_json({
            "type": "init",
            "session_id": session_id,
            "user_id": user.id,
            "username": user.username,
            "users": manager.get_users_in_room(room_name),
            "history": [
                {
                    "username": msg.user.username if hasattr(msg, 'user') and msg.user else "Unknown",
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat()
                }
                for msg in reversed(messages)
            ]
        })

        # Уведомляем всех
        await manager.broadcast_to_room(room_name, {
            "type": "user_joined",
            "user_id": user.id,
            "username": user.username,
            "users": manager.get_users_in_room(room_name)
        }, exclude_session_id=session_id)

        # Основной цикл
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
                message_type = data.get("type")

                if message_type == "chat":
                    content = data.get("content")
                    timestamp = data.get("timestamp")

                    # Сохраняем сообщение в БД
                    saved_message = await message_service.create_message(
                        room_id=room.id,
                        user_id=user.id,
                        content=content,
                        message_type="text"
                    )

                    # Отправляем всем
                    await manager.broadcast_to_room(room_name, {
                        "type": "chat",
                        "user_id": user.id,
                        "username": user.username,
                        "content": content,
                        "timestamp": timestamp or saved_message.created_at.isoformat()
                    })

                elif message_type == "webrtc_offer":
                    target_session_id = data.get("target_session_id")
                    await manager.send_to_user(room_name, target_session_id, {
                        "type": "webrtc_offer",
                        "from_session_id": session_id,
                        "from_user_id": user.id,
                        "from_username": user.username,
                        "sdp": data.get("sdp")
                    })

                elif message_type == "webrtc_answer":
                    target_session_id = data.get("target_session_id")
                    await manager.send_to_user(room_name, target_session_id, {
                        "type": "webrtc_answer",
                        "from_session_id": session_id,
                        "from_user_id": user.id,
                        "sdp": data.get("sdp")
                    })

                elif message_type == "ice_candidate":
                    target_session_id = data.get("target_session_id")
                    await manager.send_to_user(room_name, target_session_id, {
                        "type": "ice_candidate",
                        "from_session_id": session_id,
                        "candidate": data.get("candidate")
                    })

            except asyncio.TimeoutError:
                # Отправляем ping для поддержания соединения
                await websocket.send_json({"type": "ping"})
                continue

    except WebSocketDisconnect:
        # Обработка отключения
        if 'session_id' in locals():
            manager.disconnect(room_name, session_id)
            if 'room' in locals():
                await room_service.remove_user_from_room(room.id, user.id)
            await manager.broadcast_to_room(room_name, {
                "type": "user_left",
                "user_id": user.id,
                "username": user.username,
                "users": manager.get_users_in_room(room_name)
            })
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=4000, reason=str(e))