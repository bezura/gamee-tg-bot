from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.cache.redis import cached, build_key
from bot.database.models.game import GameModel


async def get_inline_games(session: AsyncSession, inline_query: str):
    """Checks if the user is in the database."""
    query = select(GameModel).order_by(GameModel.id).where(GameModel.title.ilike(f"%{inline_query}%")).limit(10)

    result = await session.execute(query)

    games = result.scalars()

    return games


async def get_game_by_offset(session: AsyncSession, offset: int):
    query = select(GameModel).offset(offset).order_by(GameModel.id).limit(1)
    result = await session.execute(query)
    game = result.scalar_one_or_none()
    return game
