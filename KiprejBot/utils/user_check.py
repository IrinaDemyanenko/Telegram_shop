from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from sqlalchemy.future import select
from database.orm_requests import orm_get_user_role

async def user_check(session: AsyncSession, telegram_id: int) -> User | None:
    """
    Проверяет, зарегистрирован ли пользователь в БД.

    session: Асинхронная сессия SQLAlchemy.
    telegram_id: Telegram ID пользователя.
    return: Объект пользователя, если найден, иначе None.
    """
    query = select(User).where(User.telegram_id == telegram_id)
    return await session.scalar(query)


async def is_registered(session: AsyncSession, telegram_id: int) -> bool:
    """
    Проверяет, зарегистрирован ли пользователь в БД.
    Возвращает True, если пользователь зарегистрирован, иначе False.
    """
    query = select(User).where(User.telegram_id == telegram_id)
    result = await session.scalar(query)

    print(f"🔍 Проверка регистрации: user_id={telegram_id}, найден={bool(result)}")  # Отладка

    return result is not None



async def is_admin(session: AsyncSession, user_id: int) -> bool:
    """Возвращает True, если пользователь администратор или суперюзер, иначе False."""
    role = await orm_get_user_role(session, user_id)
    print(f"🔍 Проверка админа: user_id={user_id}, role={role}")  # Отладочный вывод
    return role in ["admin", "superuser"]
