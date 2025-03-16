import functools
from aiogram import types
from database.db import async_session
from database.orm_requests import orm_get_user_by_telegram

# Задаем разрешенные роли для административных команд
ALLOWED_ADMIN_ROLES = {"admin", "superuser"}


def admin_required(handler):
    """
    Декоратор для проверки, что у пользователя роль admin или superuser.
    Если роль не соответствует, отправляет сообщение об отсутствии доступа.
    """
    @functools.wraps(handler)
    async def wrapper(message: types.Message, *args, **kwargs):
        telegram_id = message.from_user.id
        async with async_session() as session:
            user = await orm_get_user_by_telegram(session, telegram_id)
        if not user or user.role not in ALLOWED_ADMIN_ROLES:
            await message.answer("Доступ запрещён. Эта команда доступна только администраторам.")
            return
        return await handler(message, *args, **kwargs)
    return wrapper
