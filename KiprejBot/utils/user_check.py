from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from sqlalchemy.future import select

async def user_check(session: AsyncSession, telegram_id: int) -> User | None:
    """
    Проверяет, зарегистрирован ли пользователь в БД.

    session: Асинхронная сессия SQLAlchemy.
    telegram_id: Telegram ID пользователя.
    return: Объект пользователя, если найден, иначе None.
    """
    query = select(User).where(User.telegram_id == telegram_id)
    return await session.scalar(query)
