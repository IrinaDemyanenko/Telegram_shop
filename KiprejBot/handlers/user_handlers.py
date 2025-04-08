from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from handlers.menu_handlers import show_main_menu
from database.orm_requests import (
    orm_get_all_products,
    orm_get_user_by_telegram,
    orm_get_orders_for_user,
    orm_get_addresses_for_user
)
from database.db import async_session
from database.models import Order
from keyboards.main_menu import get_main_menu
from utils.user_check import is_admin, is_registered



user_router = Router()

@user_router.message(Command("start"))
async def start_handler(message: Message, session: AsyncSession):
    # user_id = message.from_user.id
    # admin_status = await is_admin(session, user_id)  # Проверяем, является ли пользователь администратором
    # #registered_status = await is_registered(session, user_id)  # Проверяем, зарегистрирован ли пользователь
    # await message.answer(
    #     "Добро пожаловать в магазин!\nВыберите интересующий вас раздел:",
    #     reply_markup=get_main_menu(
    #         is_admin=admin_status,
    #         )
    # )
    await message.answer("Добро пожаловать в магазин!")
    await show_main_menu(message, session)


# @user_router.message(lambda message: message.text == "🏬 Каталог")   # 📦
# async def catalog_handler(message: Message, session: AsyncSession):
#     products = await orm_get_all_products(session)
#     if products:
#         text = "Наши товары:\n"
#         for prod in products:
#             text += f"{prod.id}. {prod.name} — {prod.price} руб.\n"
#         await message.answer(text)
#     else:
#         await message.answer("Магазин пока пустой.")


# Команда для просмотра истории заказов
@user_router.message(lambda message: message.text == "🛍 Мои заказы")
async def my_orders_handler(message: Message, session: AsyncSession):
    user = await orm_get_user_by_telegram(session, message.from_user.id)
    if user:
        orders = await orm_get_orders_for_user(session, user)
        if orders:
            text = "Ваша история заказов:\n"
            for order in orders:
                text += (
                    f"Заказ #{order.id}: сумма {order.total_amount} руб, "
                    f"оплачен: {'Да' if order.is_paid else 'Нет'}, статус: {order.shipping_status or 'не указан'}\n"
                )
            await message.answer(text)
        else:
            await message.answer("У вас пока нет заказов.")
    else:
        await message.answer("Пользователь не найден. Пожалуйста, зарегистрируйтесь.")

# Команда для просмотра адресов доставки
@user_router.message(lambda message: message.text == "🏠 Мои адреса")
async def my_addresses_handler(message: Message, session: AsyncSession):
    user = await orm_get_user_by_telegram(session, message.from_user.id)
    if user:
        addresses = await orm_get_addresses_for_user(session, user)
        if addresses:
            text = "Ваши адреса доставки:\n"
            for addr in addresses:
                text += (
                    f"{addr.id}. {addr.address_line}, {addr.city}, {addr.country}"
                    f" (Почтовый индекс: {addr.postal_code or 'не указан'})\n"
                )
            await message.answer(text)
        else:
            await message.answer("У вас пока нет сохраненных адресов.")
    else:
        await message.answer("Пользователь не найден. Пожалуйста, зарегистрируйтесь.")


@user_router.message(Command("update_address"))
async def update_address_handler(message: Message):
    # Здесь можно реализовать логику добавления или обновления адреса доставки с использованием FSM
    await message.answer("Функция обновления адреса доставки в разработке.")
