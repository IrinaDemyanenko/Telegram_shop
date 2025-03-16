from aiogram import Router, types
from aiogram.filters import Command
from database.db import async_session
from database.orm_requests import orm_get_user_by_telegram
from sqlalchemy import update
from database.models import User
from utils.role_decorator import admin_required

superuser_router = Router()


@superuser_router.message(Command("set_role"))
@admin_required
async def set_role_handler(message: types.Message):
    """
    Команда для суперпользователя для обновления роли пользователя.
    Ожидается формат: /set_role <telegram_id> <role>
    Пример: /set_role 530876949 admin
    """
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Используйте: /set_role <telegram_id> <role>")
        return
    try:
        target_telegram_id = int(parts[1])
    except ValueError:
        await message.answer("Неверный формат telegram_id.")
        return
    role = parts[2].lower()
    ALLOWED_ROLES = {"user", "admin", "superuser"}
    if role not in ALLOWED_ROLES:
        await message.answer(f"Роль должна быть одной из: {', '.join(ALLOWED_ROLES)}")
        return
    async with async_session() as session:
        user = await orm_get_user_by_telegram(session, target_telegram_id)
        if not user:
            await message.answer("Пользователь не найден.")
            return
        # Обновляем роль пользователя stmt = statement
        stmt = update(User).where(User.id == user.id).values(role=role)
        await session.execute(stmt)
        await session.commit()
    await message.answer(f"Роль пользователя с telegram_id {target_telegram_id} обновлена на {role}.")

@superuser_router.message(Command("broadcast"))
async def broadcast(message: types.Message):
    # Пример: суперпользовательская команда рассылки сообщений.
    await message.answer("Суперпользовательская рассылка: сообщение отправлено всем пользователям!")

@superuser_router.message(Command("config"))
async def config(message: types.Message):
    # Пример команды для изменения настроек магазина.
    await message.answer("Суперпользовательские настройки магазина.")
