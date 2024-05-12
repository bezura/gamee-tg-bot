from pydantic import BaseModel

from bot.enums.game_types import GameType


class UserDataResponse(BaseModel):
    id: int
    money: float


class GameBaseResponse(BaseModel):
    id: int
    title: str
    description: str
    thumbnail_url: str | None


class GameResponse(GameBaseResponse):
    # game_type: GameType
    is_active: bool
