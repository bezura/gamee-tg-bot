from __future__ import annotations
from typing import TYPE_CHECKING, BinaryIO

from sqlalchemy import func, select, update

from bot.cache.redis import build_key, cached, clear_cache
from bot.core.config import settings
from bot.database.models import UserModel
import python_avatars as pa

if TYPE_CHECKING:
    from aiogram.types import User
    from sqlalchemy.ext.asyncio import AsyncSession


async def add_user(
        session: AsyncSession,
        user: User,
        referrer: str | None,
) -> None:
    """Add a new user to the database."""
    user_id: int = user.id
    first_name: str = user.first_name
    last_name: str | None = user.last_name
    username: str | None = user.username
    language_code: str | None = user.language_code
    is_premium: bool = user.is_premium or False

    photos_profile = (await user.get_profile_photos())
    avatar_url = None
    if photos_profile.total_count > 0:
        file_id: str = photos_profile.photos[0][-1].file_id
        file = await user.bot.get_file(file_id)
        file_path = file.file_path
        await user.bot.download_file(file_path, f"{settings.MEDIA_PATH}/avatar_{user_id}.png")
        avatar_url = f"/media/avatar_{user_id}.png"
    else:
        pa.Avatar.random(
            style=pa.AvatarStyle.TRANSPARENT,
            clothing=pa.ClothingType.GRAPHIC_SHIRT,
            clothing_color=pa.ClothingColor.pick_random,
            shirt_graphic=pa.ClothingGraphic.CUSTOM_TEXT,
            shirt_text=first_name
        ).render(f"{settings.MEDIA_PATH}/avatar_{user_id}.svg")
        avatar_url = f"/media/avatar_{user_id}.svg"

    new_user = UserModel(
        id=user_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        language_code=language_code,
        is_premium=is_premium,
        referrer=referrer,
        avatar_url=avatar_url
    )

    session.add(new_user)
    await session.commit()
    await clear_cache(user_exists, user_id)


async def add_money_by_id(session: AsyncSession, user_id: int, new_count_money: float) -> None:
    query = update(UserModel).where(UserModel.id == user_id).values(money=new_count_money)
    await session.execute(query)
    await session.commit()


@cached(key_builder=lambda session, user_id: build_key(user_id))
async def user_exists(session: AsyncSession, user_id: int) -> bool:
    """Checks if the user is in the database."""
    query = select(UserModel.id).filter_by(id=user_id).limit(1)

    result = await session.execute(query)

    user = result.scalar_one_or_none()
    return bool(user)


@cached(key_builder=lambda session, user_id: build_key(user_id))
async def get_first_name(session: AsyncSession, user_id: int) -> str:
    query = select(UserModel.first_name).filter_by(id=user_id)

    result = await session.execute(query)

    first_name = result.scalar_one_or_none()
    return first_name or ""


@cached(key_builder=lambda session, user_id: build_key(user_id))
async def get_language_code(session: AsyncSession, user_id: int) -> str:
    query = select(UserModel.language_code).filter_by(id=user_id)

    result = await session.execute(query)

    language_code = result.scalar_one_or_none()
    return language_code or ""


async def get_user_money(session: AsyncSession, user_id: int) -> float:
    query = select(UserModel.money).filter_by(id=user_id)

    result = await session.execute(query)

    money = result.scalar_one_or_none()
    return money or 0.0


async def get_user_data(session: AsyncSession, user_id: int):
    query = select(UserModel).filter_by(id=user_id)

    result = await session.execute(query)

    user = result.scalar_one_or_none()
    return user


async def set_language_code(
        session: AsyncSession,
        user_id: int,
        language_code: str,
) -> None:
    stmt = update(UserModel).where(UserModel.id == user_id).values(language_code=language_code)

    await session.execute(stmt)
    await session.commit()


@cached(key_builder=lambda session, user_id: build_key(user_id))
async def is_admin(session: AsyncSession, user_id: int) -> bool:
    query = select(UserModel.is_admin).filter_by(id=user_id)

    result = await session.execute(query)

    is_admin = result.scalar_one_or_none()
    return bool(is_admin)


async def set_is_admin(session: AsyncSession, user_id: int, is_admin: bool) -> None:
    stmt = update(UserModel).where(UserModel.id == user_id).values(is_admin=is_admin)

    await session.execute(stmt)
    await session.commit()


@cached(key_builder=lambda session: build_key())
async def get_all_users(session: AsyncSession) -> list[UserModel]:
    query = select(UserModel)

    result = await session.execute(query)

    users = result.scalars()
    return list(users)


@cached(key_builder=lambda session: build_key())
async def get_user_count(session: AsyncSession) -> int:
    query = select(func.count()).select_from(UserModel)

    result = await session.execute(query)

    count = result.scalar_one_or_none() or 0
    return int(count)
