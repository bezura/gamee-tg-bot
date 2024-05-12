from sqlalchemy.orm import Session

from bot.database.database import sessionmaker


async def get_session() -> Session:
    session = sessionmaker()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
