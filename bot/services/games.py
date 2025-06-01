from typing import Literal

from sqlalchemy import or_, select, asc, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.cache.redis import cached, build_key
from bot.database.models.game import GameModel


async def get_inline_games(session: AsyncSession, inline_query: str):
    """Checks if the user is in the database."""
    query = select(GameModel).order_by(GameModel.id).where(GameModel.title.ilike(f"%{inline_query}%")).limit(10)

    result = await session.execute(query)

    games = result.scalars()

    return games


async def get_game_by_offset(session: AsyncSession, offset: int, sort: Literal["asc", "desc"] = "asc"):
    query = select(GameModel).offset(offset).order_by(GameModel.id).limit(1)
    if sort == "asc":
        query = query.order_by(asc(GameModel.id))
    else:
        query = query.order_by(desc(GameModel.id))
    result = await session.execute(query)
    game = result.scalar_one_or_none()
    return game


async def get_games_count(session: AsyncSession):
    query = select(func.count(GameModel.id))
    result = await session.execute(query)
    return result.scalar()


async def get_game_by_id(session: AsyncSession, game_id: int):
    query = select(GameModel).where(GameModel.id == game_id).limit(1)
    result = await session.execute(query)
    game = result.scalar_one_or_none()
    return game
