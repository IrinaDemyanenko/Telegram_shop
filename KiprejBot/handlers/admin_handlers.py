
import pandas as pd
from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from analytics.analytics import get_popular_products
from database.models import Order, User, Product
from database.db import async_session
from database.orm_requests import orm_add_product
from utils.role_decorator import admin_required
from aiogram.types import FSInputFile
from database.orm_requests import orm_get_all_products_with_variants
from aiogram.types import Message



admin_router = Router()


# =======================
# Команды для управления пользователями
# =======================
@admin_router.message(Command("list_users"))
@admin_required
async def list_users_handler(message: types.Message):
    """Выводит список всех зарегистрированных пользователей."""
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
    if users:
        text = "Список пользователей:\n"
        for user in users:
            text += (
                f"ID: {user.id}, Telegram ID: {user.telegram_id}, Name: {user.full_name}, Email: {user.email}\n"
            )
        await message.answer(text)
    else:
        await message.answer("Пользователей пока нет.")

@admin_router.message(Command("user_details"))
@admin_required
async def user_details_handler(message: types.Message):
    """Выводит подробности о пользователе.
    Ожидается: /user_details <user_id>
    Пример: /user_details 4 (ID в БД, а не Telegram ID)
    """
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Используйте: /user_details <user_id>")
        return
    try:
        user_id = int(parts[1])
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar()
        if user:
            text = (
                f"Детали пользователя:\n"
                f"ID: {user.id}\n"
                f"Telegram ID: {user.telegram_id}\n"
                f"ФИО: {user.full_name}\n"
                f"Email: {user.email}\n"
                f"Телефон: {user.phone}\n"
                f"Email: {user.role.value}\n"  # тк нужно получить значение RoleEnum.USER
                f"Зарегистрирован: {user.created_at}\n"
            )
            await message.answer(text)
        else:
            await message.answer("Пользователь не найден.")
    except Exception as e:
        await message.answer("Ошибка при получении информации о пользователе.")

# Команда для удаления товара (базовый пример)
@admin_router.message(Command("delete_product"))
@admin_required
async def delete_product_handler(message: types.Message):
    # Ожидается: /delete_product <id>
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Используйте: /delete_product <id>")
        return
    try:
        product_id = int(parts[1])
        async with async_session() as session:
            result = await session.execute(select(Product).where(Product.id == product_id))
            product = result.scalar()
            if product:
                await session.delete(product)
                await session.commit()
                await message.answer(f"Продукт с id {product_id} удален.")
            else:
                await message.answer("Продукт не найден.")
    except Exception as e:
        await message.answer("Ошибка при удалении продукта.")


# =======================
# Дополнительные команды: для выгрузки всех товаров из БД в Excel
# =======================
@admin_router.message(Command("all_products"))
@admin_required
async def list_all_products(message: Message, session: AsyncSession):
    """Команда позволяет выгрузить информацию о всех товаров из БД,
    в ответ на команду бот сформирует и отправит Excel file.
    Здесь товары сгруппированы по категориям, со всеми вариантами.
    """
    products = await orm_get_all_products_with_variants(session)

    if not products:
        await message.answer("❌ Нет товаров в базе данных.")
        return

    data = []
    for product in products:
        base_info = {
            "ID товара": product.id,
            "Категория": product.category.name if product.category else "—",
            "Название": product.name,
            "Описание": product.description or "—",
            "Бренд": product.brand or "—",
            "Базовая цена": product.price
        }

        if product.variants:
            for variant in product.variants:
                final_price = (
                    product.price + variant.additional_price
                ) * (1 - variant.discount_percent / 100)

                data.append({
                    **base_info,
                    "Размер": variant.size,
                    "Цвет": variant.color,
                    "Наценка": variant.additional_price,
                    "Скидка": f"{variant.discount_percent}%",
                    "Итоговая цена": round(final_price, 2),
                    "Остаток на складе": variant.stock
                })
        else:
            data.append({**base_info})

    df = pd.DataFrame(data)

    # Сохраняем в файл Excel
    file_path = "products_with_variants.xlsx"
    df.to_excel(file_path, index=False)

    await message.answer_document(
        FSInputFile(file_path),
        caption="📦 Все товары с вариантами по категориям:"
        )
# =======================
# Дополнительные команды для управления заказами и пользователями
# =======================

@admin_router.message(Command("list_orders"))
@admin_required
async def list_orders_handler(message: types.Message):
    """Выводит список всех заказов."""
    async with async_session() as session:
        result = await session.execute(select(Order))
        orders = result.scalars().all()
    if orders:
        text = "Список заказов:\n"
        for order in orders:
            text += (
                f"ID: {order.id}, User ID: {order.user_id}, Total: {order.total_amount} руб, "
                f"Paid: {order.is_paid}, Status: {order.shipping_status}\n"
            )
        await message.answer(text)
    else:
        await message.answer("Заказов пока нет.")

@admin_router.message(Command("order_details"))
@admin_required
async def order_details_handler(message: types.Message):
    """Выводит подробности заказа по ID.
    Ожидается формат: /order_details <order_id>
    """
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Используйте: /order_details <order_id>")
        return
    try:
        order_id = int(parts[1])
        async with async_session() as session:
            result = await session.execute(select(Order).where(Order.id == order_id))
            order = result.scalar()
        if order:
            text = (
                f"Детали заказа {order.id}:\n"
                f"User ID: {order.user_id}\n"
                f"Total Amount: {order.total_amount} руб\n"
                f"Paid: {order.is_paid}\n"
                f"Shipping Status: {order.shipping_status}\n"
                f"Payment Method: {order.payment_method}\n"
                f"Created At: {order.created_at}\n"
            )
            await message.answer(text)
        else:
            await message.answer("Заказ не найден.")
    except Exception as e:
        await message.answer("Ошибка при получении деталей заказа.")

@admin_router.message(Command("update_order"))
@admin_required
async def update_order_handler(message: types.Message):
    """
    Обновляет статус заказа.
    Ожидается формат: /update_order <order_id> <new_status> [yes/no]
    Последний параметр (yes/no) определяет, оплачён ли заказ.
    """
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Используйте: /update_order <order_id> <new_status> [yes/no]")
        return
    try:
        order_id = int(parts[1])
        new_status = parts[2]
        is_paid = None
        if len(parts) == 4:
            is_paid = True if parts[3].lower() == "yes" else False
        async with async_session() as session:
            # Обновление shipping_status
            stmt = update(Order).where(Order.id == order_id).values(shipping_status=new_status)
            await session.execute(stmt)
            # Если указан параметр оплаты, обновляем его
            if is_paid is not None:
                stmt2 = update(Order).where(Order.id == order_id).values(is_paid=is_paid)
                await session.execute(stmt2)
            await session.commit()
        await message.answer(f"Заказ {order_id} обновлен: статус '{new_status}', оплата: {is_paid if is_paid is not None else 'без изменений'}.")
    except Exception as e:
        await message.answer("Ошибка при обновлении заказа.")


@admin_router.message(Command("popular_products"))
@admin_required
async def popular_products_handler(message: types.Message):
    """
    Выводит список самых популярных товаров по количеству просмотров.
    Использует модуль аналитики для получения статистики.
    """
    async with async_session() as session:
        popular = await get_popular_products(session, limit=5)
    if popular:
        text = "Наиболее популярные товары:\n"
        for product, count in popular:
            text += f"{product.name}: {count} просмотров\n"
        await message.answer(text)
    else:
        await message.answer("Нет данных о просмотрах товаров.")
