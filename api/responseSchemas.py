from typing import Dict, Any

from pydantic import BaseModel, Field


class UserDataResponse(BaseModel):
    id: int
    money: float
    avatar_url: str | None


class GameBaseResponse(BaseModel):
    id: int
    title: str
    description: str
    thumbnail_url: str | None


class GameResponse(GameBaseResponse):
    is_active: bool
    websocket_uri: str | None
    front_uri: str | None


class UserDataForGameResponse(BaseModel):
    last_name: str | None
    first_name: str
    username: str
    avatar_url: str | None
    is_ready: bool = Field(default=False)


class PlayingGameResponse(BaseModel):
    game_id: str
    title: str
    description: str
    websocket_uri: str
    bet: int
    count_players: int
    connected_players: Dict[int, UserDataForGameResponse] = Field({})
    current_player_id: str | None = Field(None)
    game_started: bool = Field(False)
    game_progress: Any = Field(None)
    game_finished: bool = Field(False)
    winner_id: str | None = Field(None)
