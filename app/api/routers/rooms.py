from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.room import RoomCreate, RoomResponse
from app.services.room_service import RoomService, get_room_service
from app.api.routers.auth import get_current_user
from app.schemas.user import UserResponse
from app.db.base import get_db

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("/", response_model=List[dict])
async def get_rooms(
        current_user: UserResponse = Depends(get_current_user),
        room_service: RoomService = Depends(get_room_service),
        db: AsyncSession = Depends(get_db)
):
    """Получить список всех доступных комнат"""
    rooms = await room_service.get_all_rooms()

    # Добавляем количество участников для каждой комнаты
    result = []
    for room in rooms:
        members = await room_service.get_room_members(room.id)
        result.append({
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "created_by": room.created_by,
            "created_at": room.created_at.isoformat() if room.created_at else None,
            "member_count": len(members),
            "is_private": room.is_private
        })

    return result


@router.post("/", response_model=dict)
async def create_room(
        room_data: RoomCreate,
        current_user: UserResponse = Depends(get_current_user),
        room_service: RoomService = Depends(get_room_service)
):
    """Создать новую комнату"""
    # Проверяем, существует ли комната с таким именем
    existing_room = await room_service.get_room_by_name(room_data.name)
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room with this name already exists"
        )

    room = await room_service.create_room(room_data, current_user.id)

    return {
        "id": room.id,
        "name": room.name,
        "description": room.description,
        "created_by": room.created_by,
        "created_at": room.created_at.isoformat() if room.created_at else None,
        "member_count": 1,
        "is_private": room.is_private
    }


@router.get("/{room_id}", response_model=dict)
async def get_room(
        room_id: int,
        current_user: UserResponse = Depends(get_current_user),
        room_service: RoomService = Depends(get_room_service)
):
    """Получить информацию о комнате"""
    room = await room_service.get_room(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    members = await room_service.get_room_members(room_id)

    return {
        "id": room.id,
        "name": room.name,
        "description": room.description,
        "created_by": room.created_by,
        "created_at": room.created_at.isoformat() if room.created_at else None,
        "member_count": len(members),
        "is_private": room.is_private
    }


@router.post("/{room_id}/join")
async def join_room(
        room_id: int,
        current_user: UserResponse = Depends(get_current_user),
        room_service: RoomService = Depends(get_room_service)
):
    """Присоединиться к комнате"""
    room = await room_service.get_room(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    await room_service.add_user_to_room(room_id, current_user.id)
    return {"message": "Joined room successfully"}


@router.post("/{room_id}/leave")
async def leave_room(
        room_id: int,
        current_user: UserResponse = Depends(get_current_user),
        room_service: RoomService = Depends(get_room_service)
):
    """Покинуть комнату"""
    await room_service.remove_user_from_room(room_id, current_user.id)
    return {"message": "Left room successfully"}