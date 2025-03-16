import re
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from database.models import Product, Category, ProductImage, ProductVariant
from database.orm_requests import orm_get_all_categories, orm_get_category_by_name, save_product_image
from keyboards.admin_keyboards import admin_menu
from utils.role_decorator import admin_required


admin_router_product_management = Router()  # Создаём роутер для управления товарами


class AddProduct(StatesGroup):  # Определяем состояния для машины состояний (FSM)
    category = State()
    name = State()
    description = State()
    price = State()
    brand = State()
    images = State()
    variants = State()
    confirm = State()


# Хэндлер для начала добавления товара
@admin_router_product_management.message(Command("add_product"))
@admin_required
async def add_product_start(message: Message, state: FSMContext, session: AsyncSession):
    categories = await orm_get_all_categories(session)

    if not categories:
        await message.answer("Нет доступных категорий. Сначала добавьте категории.")
        return

    # Добавляем клавиатуру с категориями товаров
    category_buttons = [types.KeyboardButton(c.name) for c in categories]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add(*category_buttons)

    await message.answer("Выберите категорию:", reply_markup=markup)
    await state.set_state(AddProduct.category)

# Хэндлер для получения категории товара
@admin_router_product_management.message(AddProduct.category)
async def add_product_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Введите название товара:")
    await state.set_state(AddProduct.name)

# Хэндлер для получения названия товара
@admin_router_product_management.message(AddProduct.name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание товара:")
    await state.set_state(AddProduct.description)

# Хэндлер для получения описания товара
@admin_router_product_management.message(AddProduct.description)
async def add_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите цену товара:")
    await state.set_state(AddProduct.price)

# Хэндлер для получения цены товара
@admin_router_product_management.message(AddProduct.price)
async def add_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await message.answer("Введите бренд товара:")
        await state.set_state(AddProduct.brand)
    except ValueError:
        await message.answer("Некорректная цена. Введите число.")

# Хэндлер для получения бренда товара
@admin_router_product_management.message(AddProduct.brand)
async def add_product_brand(message: Message, state: FSMContext):
    await state.update_data(brand=message.text)
    await message.answer("Отправьте до 10 изображений (по одному). Когда закончите, отправьте команду /done.")
    await state.set_state(AddProduct.images)

# Хэндлер для загрузки изображений товара
@admin_router_product_management.message(AddProduct.images, content_types=[ContentType.PHOTO, ContentType.TEXT])
async def add_product_images(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if "images" not in data:
            data["images"] = []

        if message.content_type == ContentType.PHOTO:
            if len(data["images"]) < 10:
                data["images"].append(message.photo[-1].file_id)
                await message.answer(f"Добавлено изображение {len(data['images'])}/10")
            else:
                await message.answer("Максимум 10 изображений!")
        elif message.text == "/done":
            await message.answer("Теперь добавьте варианты товара (размер, цвет, цена, скидка, количество).")
            await state.set_state(AddProduct.variants)


# Хэндлер для начала добавления варианта товара
@admin_router_product_management.message(AddProduct.variants)
async def add_variant_start(message: Message, state: FSMContext):
    await message.answer("Введите размер товара (например, S, M, L, XL):")
    await state.set_state(AddProduct.variant_size)

# Получаем размер
@admin_router_product_management.message(AddProduct.variant_size)
async def add_variant_size(message: Message, state: FSMContext):
    size = message.text.strip()
    if not size:
        await message.answer("Размер не может быть пустым. Введите размер ещё раз:")
        return
    await state.update_data(size=size)
    await message.answer("Введите цвет товара (например, Красный, Синий, Чёрный):")
    await state.set_state(AddProduct.variant_color)

# Получаем цвет
@admin_router_product_management.message(AddProduct.variant_color)
async def add_variant_color(message: Message, state: FSMContext):
    color = message.text.strip()
    await state.update_data(color=color)
    await message.answer("Введите наценку за вариант в числовом формате (например, 200):")
    await state.set_state(AddProduct.variant_additional_price)

# Получаем наценку
@admin_router_product_management.message(AddProduct.variant_additional_price)
async def add_variant_additional_price(message: Message, state: FSMContext):
    try:
        additional_price = float(message.text.strip())
        await state.update_data(additional_price=additional_price)
        await message.answer("Введите скидку в процентах (например, 10):")
        await state.set_state(AddProduct.variant_discount)
    except ValueError:
        await message.answer("Некорректный ввод. Введите числовое значение наценки:")

# Получаем скидку
@admin_router_product_management.message(AddProduct.variant_discount)
async def add_variant_discount(message: Message, state: FSMContext):
    try:
        discount_percent = float(message.text.strip())
        if discount_percent < 0 or discount_percent > 100:
            raise ValueError
        await state.update_data(discount_percent=discount_percent)
        await message.answer("Введите количество товара на складе:")
        await state.set_state(AddProduct.variant_stock)
    except ValueError:
        await message.answer("Некорректный ввод. Введите скидку в диапазоне 0-100:")

# Получаем количество на складе
@admin_router_product_management.message(AddProduct.variant_stock)
async def add_variant_stock(message: Message, state: FSMContext):
    try:
        stock = int(message.text.strip())
        if stock < 0:
            raise ValueError
        async with state.proxy() as data:
            if "variants" not in data:
                data["variants"] = []
            data["variants"].append({
                "size": data["size"],
                "color": data["color"],
                "additional_price": data["additional_price"],
                "discount_percent": data["discount_percent"],
                "stock": stock,
            })
        await message.answer("Вариант добавлен! Введите новый размер или напишите /done, чтобы завершить.")
        await state.set_state(AddProduct.variants)
    except ValueError:
        await message.answer("Некорректный ввод. Введите целое положительное число для количества на складе:")

# Завершаем добавление вариантов и подтверждаем товар
@admin_router_product_management.message(Command("done"))
async def confirm_variants(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if "variants" not in data or not data["variants"]:
            await message.answer("Вы не добавили ни одного варианта. Введите хотя бы один вариант или напишите /cancel для отмены.")
            return
    await message.answer("Все варианты добавлены! Теперь подтвердите сохранение товара.", reply_markup=admin_menu)
    await state.set_state(AddProduct.confirm)

# Хэндлер для получения вариантов товара (размер, цвет, цена и т. д.)
# @admin_router_product_management.message(AddProduct.variants)
# async def add_product_variants(message: Message, state: FSMContext):
#     parts = message.text.split(",")
#     if len(parts) < 3:
#         await message.answer("Введите данные в формате: Размер, Цвет, Наценка, Скидка, Количество")
#         return

#     size, color, additional_price, discount_percent, stock = parts[:5]

#     try:
#         additional_price = float(additional_price)
#         discount_percent = float(discount_percent)
#         stock = int(stock)
#     except ValueError:
#         await message.answer("Некорректный ввод. Убедитесь, что числа введены правильно.")
#         return

#     async with state.proxy() as data:
#         if "variants" not in data:
#             data["variants"] = []
#         data["variants"].append({
#             "size": size,
#             "color": color,
#             "additional_price": additional_price,
#             "discount_percent": discount_percent,
#             "stock": stock,
#         })

#     await message.answer("Добавлено! Введите ещё один вариант или напишите /done.")

# Хэндлер для подтверждения и сохранения товара
@admin_router_product_management.message(AddProduct.confirm)
async def confirm_product(message: Message, state: FSMContext, session: AsyncSession):
    async with state.proxy() as data:  # работаем с fsm как со словарём, читаеми меняем данные
        # Проверяем категорию
        category = await orm_get_category_by_name(session, category_name=data["category"])

        if not category:
            await message.answer("Ошибка: выбранная категория не найдена в базе данных.")
            return

        new_product = Product(
            name=data["name"],
            description=data["description"],
            price=data["price"],
            brand=data["brand"],
            category_id=category.id,
        )

        session.add(new_product)
        await session.commit()

        # Проверяем изображения
        if "images" in data and data["images"]:
            for file_id in data["images"]:
                file = await message.bot.get_file(file_id)
                await save_product_image(file, new_product.id, session)

        # Проверяем варианты товара
        if "variants" in data and data["variants"]:
            for variant in data["variants"]:
                new_variant = ProductVariant(product_id=new_product.id, **variant)
                session.add(new_variant)

        await session.commit()
        await message.answer("✅ Товар добавлен!", reply_markup=admin_menu)

    await state.clear()
