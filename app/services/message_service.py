from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from typing import List, Optional

from app.db.base import get_db
from app.models.message import Message
from app.schemas.message import MessageCreate


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(
            self,
            room_id: int,
            user_id: int,
            content: str,
            message_type: str = "text"
    ) -> Message:
        """Создание и сохранение сообщения"""
        message = Message(
            room_id=room_id,
            user_id=user_id,
            content=content,
            message_type=message_type
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_room_messages(
            self,
            room_id: int,
            limit: int = 100,
            offset: int = 0
    ) -> List[Message]:
        """Получить историю сообщений комнаты"""
        result = await self.db.execute(
            select(Message)
            .where(Message.room_id == room_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """Получить сообщение по ID"""
        result = await self.db.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def delete_message(self, message_id: int) -> bool:
        """Удалить сообщение"""
        message = await self.get_message_by_id(message_id)
        if message:
            await self.db.delete(message)
            await self.db.commit()
            return True
        return False


# Dependency
async def get_message_service(db: AsyncSession = Depends(get_db)):
    return MessageService(db)