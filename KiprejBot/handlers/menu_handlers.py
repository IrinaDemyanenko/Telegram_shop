import asyncio
import random
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from keyboards.main_menu import get_main_menu
from keyboards.admin_keyboards import product_menu, admin_main_menu
from utils.user_check import is_admin, is_registered
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User  # Импорт модели пользователя
from database.db import async_session  # Импорт сессии для работы с БД
from utils.navigation import go_to_main_menu
from utils.role_decorator import admin_required
from keyboards.admin_keyboards import admin_main_menu, category_menu, product_menu





menu_router = Router()


@menu_router.message(Command("menu"))
@menu_router.message(F.text == "Меню")  # меню вызывается и по тексту Меню
async def show_main_menu(message: Message, session: AsyncSession):
    """Отображает главное меню с учётом роли пользователя и регистрации."""
    user_id = message.from_user.id

    # Проверяем статус пользователя
    admin_status = await is_admin(session, user_id)  # Проверяем, является ли пользователь администратором

    # Отображаем актуальное меню
    text_variants = ["Главное меню", "Меню", "Меню магазина", "Магазин"]
    await message.answer(
        random.choice(text_variants),
        reply_markup=get_main_menu(
            is_admin=admin_status,
            )
        )

# Переход в админ-меню по кнопке из главного меню
@menu_router.message(Command("admin_menu"))
@menu_router.message(F.text == "🔧 Админ-меню")
async def show_admin_menu(message: Message, session: AsyncSession):
    """Отображает админ-меню (только для администраторов)."""
    user_id = message.from_user.id
    admin_status = await is_admin(session, user_id)

    if admin_status:
        await message.answer("🔧 Админ-меню:", reply_markup=admin_main_menu)
    else:
        await message.answer("❌ У вас нет прав доступа к админ-меню.")


# Переход в меню управления категориями
@menu_router.message(F.text == "📂 Управление категориями")
@admin_required
async def category_management_menu(message: Message):
    await message.answer("Меню управления категориями:", reply_markup=category_menu)

# Переход в меню управления товарами
@menu_router.message(F.text == "📦 Управление товарами")
@admin_required
async def product_management_menu(message: Message):
    await message.answer("Меню управления товарами:", reply_markup=product_menu)

# Возврат в главное меню
@menu_router.message(F.text == "🔙 Выйти в главное меню")
@menu_router.message(F.text == "Назад в главное меню")
@admin_required
async def back_to_main_menu(message: Message, session: AsyncSession):
    await go_to_main_menu(message, session)
