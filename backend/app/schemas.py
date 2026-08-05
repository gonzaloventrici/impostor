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
    status: str
    players: list[PlayerOut]


class StartGameRequest(BaseModel):
    host_token: str
    num_spies: int
    category_id: Optional[int] = None
    discuss_seconds: Optional[int] = 60
    vote_seconds: Optional[int] = 45
    rounds_to_win: Optional[int] = None


class CategoryOut(BaseModel):
    id: int
    name: str


class MyRoleResponse(BaseModel):
    is_spy: bool
    word: Optional[str] = None


class VoteRequest(BaseModel):
    player_id: str
    player_token: str
    target_id: str