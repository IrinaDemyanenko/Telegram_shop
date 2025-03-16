from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker


class DataBaseSession(BaseMiddleware):
    """Session management layer."""
    # создаём сессию, как промежуточный слой мд событием и хэндлером
    # создаём session_pool куда и передаём sessionmaker
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool  # экземпляр сессии

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,  # чтобы сессия подходила для любого хэндлера
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            data['session'] = session  # сессия это и есть подключение к БД
            return await handler(event, data)
            # теперь по параметру session (как message, state) будет доступна сессия
            # подключим к основному роутеру, хотя можно и к любому второстепенному роутеру


# Подключения к БД через middleware. Автоматически создаёт сессию для
# каждого обновления и прикрепляет её к словарю data под ключом "session",
# что позволяет в обработчиках использовать эту сессию (подключение к БД)
# без явного создания через async with async_session() as session.
