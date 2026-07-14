from pydantic import BaseModel
from typing import Optional


class CreateRoomResponse(BaseModel):
    room_code: str
    host_token: str


class JoinRoomRequest(BaseModel):
    name: str


class JoinRoomResponse(BaseModel):
    player_token: str
    player_id: str


class PlayerOut(BaseModel):
    player_id: str
    name: str


class RoomStateResponse(BaseModel):
    room_code: str
    status: str  # "lobby" | "started"
    players: list[PlayerOut]


class StartGameRequest(BaseModel):
    host_token: str
    num_spies: int
    category_id: Optional[int] = None  # None = aleatoria


class CategoryOut(BaseModel):
    id: int
    name: str


class MyRoleResponse(BaseModel):
    is_spy: bool
    word: Optional[str] = None  # None si es espía
