# ruff: noqa: TCH001, TCH003, A003, F821
from __future__ import annotations

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.models.base import Base, created_at, int_pk


class GameModel(Base):
    __tablename__ = "games"
    id: Mapped[int_pk]
    title: Mapped[str]
    description: Mapped[str]
    thumbnail_url: Mapped[str | None]

    is_active: Mapped[bool] = mapped_column(server_default="0")

    websocket_uri: Mapped[str | None]
    front_uri: Mapped[str | None]

    max_players: Mapped[int] = mapped_column(server_default="2")


class UserGameModel(Base):
    __tablename__ = "user_games"
    id: Mapped[int_pk]
    user_id: Mapped[int_pk]
    game_id: Mapped[int_pk]

    score: Mapped[float]
    bet: Mapped[float]
    opponents: Mapped[list[int] | None]
