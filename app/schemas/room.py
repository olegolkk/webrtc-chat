from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.user import UserResponse


class RoomBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_private: Optional[bool] = None


class RoomResponse(RoomBase):
    id: int
    created_by: int
    created_at: datetime
    members: List[UserResponse] = []
    member_count: int = 0

    class Config:
        from_attributes = True