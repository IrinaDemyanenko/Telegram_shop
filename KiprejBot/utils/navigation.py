from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession
from keyboards.main_menu import get_main_menu
from keyboards.admin_keyboards import admin_main_menu
from utils.user_check import is_admin


async def go_to_main_menu(message: types.Message, session: AsyncSession):
    """Переход в главное меню с учётом роли пользователя."""
    user_id = message.from_user.id
    admin_status = await is_admin(session, user_id)

    await message.answer(
        "Вы вернулись в главное меню.",
        reply_markup=get_main_menu(is_admin=admin_status)
    )


async def go_to_admin_menu(message: types.Message, session: AsyncSession):
    """Переход в админ-меню (если у пользователя есть права)."""
    user_id = message.from_user.id
    admin_status = await is_admin(session, user_id)

    if admin_status:
        await message.answer(
            "🔧 Вы в админ-меню:",
            reply_markup=admin_main_menu
        )
    else:
        await message.answer("⛔ У вас нет прав доступа к админ-меню.")
