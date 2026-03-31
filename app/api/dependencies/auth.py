from fastapi import WebSocket, HTTPException, status
from typing import Optional
from app.core.security import decode_token

async def get_user_from_token(websocket: WebSocket, token: str) -> Optional[int]:
    """Получить user_id из JWT токена в WebSocket"""
    payload = decode_token(token)
    if payload:
        user_id = payload.get("sub")
        if user_id:
            return int(user_id)
    return None

async def get_token_from_websocket(websocket: WebSocket) -> Optional[str]:
    """Получить токен из WebSocket запроса"""
    # Токен может быть в query параметре или в заголовках
    token = websocket.query_params.get("token")
    return token