from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
from app.models.room import Room, room_members
from app.models.user import User
from app.schemas.room import RoomCreate
from fastapi import Depends
from app.db.base import get_db


class RoomService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_room(self, room_data: RoomCreate, creator_id: int) -> Room:
        """Создание новой комнаты"""
        room = Room(
            name=room_data.name,
            description=room_data.description,
            created_by=creator_id,
            is_private=room_data.is_private
        )
        self.db.add(room)
        await self.db.commit()
        await self.db.refresh(room)

        # Добавляем создателя в участники
        await self.add_user_to_room(room.id, creator_id)

        return room

    async def get_room(self, room_id: int) -> Optional[Room]:
        """Получить комнату по ID"""
        result = await self.db.execute(
            select(Room).where(Room.id == room_id)
        )
        return result.scalar_one_or_none()

    async def get_room_by_name(self, name: str) -> Optional[Room]:
        """Получить комнату по имени"""
        result = await self.db.execute(
            select(Room).where(Room.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all_rooms(self) -> List[Room]:
        """Получить все публичные комнаты"""
        result = await self.db.execute(
            select(Room)
            .where(Room.is_private == False)
            .order_by(desc(Room.created_at))
        )
        return result.scalars().all()

    async def get_or_create_room(self, name: str, creator_id: int) -> Room:
        """Получить комнату или создать если не существует"""
        room = await self.get_room_by_name(name)
        if not room:
            room = await self.create_room(
                RoomCreate(name=name, is_private=False),
                creator_id
            )
        return room

    async def get_user_rooms(self, user_id: int) -> List[Room]:
        """Получить все комнаты пользователя"""
        result = await self.db.execute(
            select(Room)
            .join(room_members)
            .where(room_members.c.user_id == user_id)
            .order_by(desc(Room.created_at))
        )
        return result.scalars().all()

    async def add_user_to_room(self, room_id: int, user_id: int) -> bool:
        """Добавить пользователя в комнату"""
        # Проверяем, существует ли комната
        room = await self.get_room(room_id)
        if not room:
            return False

        # Проверяем, не добавлен ли уже
        result = await self.db.execute(
            select(room_members).where(
                and_(
                    room_members.c.room_id == room_id,
                    room_members.c.user_id == user_id
                )
            )
        )
        if result.first():
            return True  # Уже в комнате

        # Добавляем
        await self.db.execute(
            room_members.insert().values(room_id=room_id, user_id=user_id)
        )
        await self.db.commit()
        return True

    async def remove_user_from_room(self, room_id: int, user_id: int) -> bool:
        """Удалить пользователя из комнаты"""
        # Проверяем, существует ли связь
        result = await self.db.execute(
            select(room_members).where(
                and_(
                    room_members.c.room_id == room_id,
                    room_members.c.user_id == user_id
                )
            )
        )
        if not result.first():
            return False

        # Удаляем
        await self.db.execute(
            room_members.delete().where(
                and_(
                    room_members.c.room_id == room_id,
                    room_members.c.user_id == user_id
                )
            )
        )
        await self.db.commit()
        return True

    async def get_room_members(self, room_id: int) -> List[User]:
        """Получить всех участников комнаты"""
        result = await self.db.execute(
            select(User)
            .join(room_members)
            .where(room_members.c.room_id == room_id)
        )
        return result.scalars().all()

    async def get_room_member_count(self, room_id: int) -> int:
        """Получить количество участников комнаты"""
        result = await self.db.execute(
            select(room_members).where(room_members.c.room_id == room_id)
        )
        return len(result.fetchall())

    async def delete_room(self, room_id: int) -> bool:
        """Удалить комнату"""
        room = await self.get_room(room_id)
        if not room:
            return False

        await self.db.delete(room)
        await self.db.commit()
        return True

    async def update_room(self, room_id: int, **kwargs) -> Optional[Room]:
        """Обновить информацию о комнате"""
        room = await self.get_room(room_id)
        if not room:
            return None

        for key, value in kwargs.items():
            if hasattr(room, key):
                setattr(room, key, value)

        await self.db.commit()
        await self.db.refresh(room)
        return room


# Dependency
async def get_room_service(db: AsyncSession = Depends(get_db)):
    return RoomService(db)