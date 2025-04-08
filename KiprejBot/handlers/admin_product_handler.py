import re
from collections import defaultdict
from types import SimpleNamespace
from aiogram.types import Message
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Product, Category, ProductImage, ProductVariant
from database.orm_requests import orm_delete_product, orm_delete_product_images, orm_delete_product_variants, orm_get_all_categories, orm_get_all_products, orm_get_category_by_name, orm_save_product_image
from keyboards.admin_keyboards import (
    product_menu,
    get_category_keyboard,
    done_keyboard,
    variant_done_keyboard,
    confirm_product_keyboard)
from utils.role_decorator import admin_required
from utils.validation import is_valid_integer
from database.orm_requests import orm_get_product_by_id
import os
from config import UPLOAD_DIR  # если нужно указывать путь до файлов локально


admin_router_product_handler = Router()  # Создаём роутер для управления товарами


def format_product_info(product: Product, category_name: str = None) -> str:
    return (
        f"<b>📋 Название:</b> {product.name}\n"
        f"<b>🆔 ID:</b> {product.id}\n"
        f"<b>📝 Описание:</b> {product.description or '–'}\n"
        f"<b>💰 Цена:</b> {product.price} руб.\n"
        f"<b>🏷 Бренд:</b> {product.brand or '–'}\n"
        f"<b>📂 Категория:</b> {category_name or (product.category.name if product.category else '–')}"
    )

def format_variant_info(variant: ProductVariant, base_price: float = None) -> str:
    final_price = "–"
    try:
        if base_price is None:
            # Попробуем через связанный продукт (если он есть), но его нет, тк связанных таблиц нет!!!
            base_price = variant.product.price
        final_price = base_price + variant.additional_price
        final_price -= final_price * (variant.discount_percent / 100)
    except Exception:
        pass

    return (
        f"<b>📐 Размер:</b> {variant.size}\n"
        f"<b>🎨 Цвет:</b> {variant.color or '–'}\n"
        f"<b>💸 Наценка:</b> {variant.additional_price} руб.\n"
        f"<b>🔖 Скидка:</b> {variant.discount_percent}%\n"
        f"<b>📦 На складе:</b> {variant.stock} шт.\n"
        f"<b>🧾 Итоговая цена:</b> {round(final_price, 2) if final_price != '–' else '–'} руб."
    ) # итоговая цена не считается, тк у fake_product нет связи с таблицами!!!

async def send_product_preview(data: dict, message: Message, bot: Bot):
    """Отправляет предпросмотр товара со всеми вариантами и первым изображением."""
    # Подготавливаем временный объект категории
    fake_category = SimpleNamespace(name=data.get("category"))

    # Создаём временный объект товара
    fake_product = Product(
        name=data.get("name"),
        description=data.get("description"),
        price=data.get("price"),
        brand=data.get("brand"),
    )
    category_name = data.get("category")  # просто строка тк вызывала ошибку из-за связи таблиц

    await message.answer("🔍 <b>Предпросмотр товара:</b>", parse_mode="HTML")
    await message.answer(
        format_product_info(fake_product, category_name=category_name),
        parse_mode="HTML"
        )

    # Отправляем первое изображение, если есть
    if data.get("images"):
        await message.answer_photo(data["images"][0])

    # Отправляем все варианты
    if data.get("variants"):
        await message.answer("<b>🧩 Варианты товара:</b>", parse_mode="HTML")
        for i, variant in enumerate(data["variants"], start=1):
            fake_variant = ProductVariant(
                size=variant["size"],
                color=variant["color"],
                additional_price=variant["additional_price"],
                discount_percent=variant["discount_percent"],
                stock=variant["stock"]
            )
            text = f"<b>Вариант {i}:</b>\n" + format_variant_info(fake_variant)
            await message.answer(text, parse_mode="HTML")

    # Кнопки подтверждения
    await message.answer(
        "Подтвердите сохранение товара:",
        reply_markup=confirm_product_keyboard)


class AddProduct(StatesGroup):  # Определяем состояния для машины состояний (FSM)
    """Описывает состояния для добавления товара в БД."""
    category = State()
    name = State()
    description = State()
    price = State()
    brand = State()
    images = State()
    variants = State()
    variant_size = State()
    variant_color = State()
    variant_additional_price = State()
    variant_discount = State()
    variant_stock = State()
    confirm = State()


# Хэндлер для начала добавления товара
@admin_router_product_handler.message(Command("add_product"))
@admin_router_product_handler.message(F.text == "Добавить товар")
@admin_required
async def add_product_start(message: Message, state: FSMContext, session: AsyncSession):
    categories = await orm_get_all_categories(session)

    if not categories:
        await message.answer("Нет доступных категорий. Сначала добавьте категории.")
        return

    # Добавляем клавиатуру с категориями товаров
    # category_buttons = [types.KeyboardButton(c.name) for c in categories]
    # markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add(*category_buttons)
    markup = get_category_keyboard(categories)

    await message.answer("Выберите категорию:", reply_markup=markup)
    await state.set_state(AddProduct.category)

# Хэндлер для получения категории товара
@admin_router_product_handler.message(AddProduct.category)
async def add_product_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Введите название товара:")
    await state.set_state(AddProduct.name)

# Хэндлер для получения названия товара
@admin_router_product_handler.message(AddProduct.name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание товара:")
    await state.set_state(AddProduct.description)

# Хэндлер для получения описания товара
@admin_router_product_handler.message(AddProduct.description)
async def add_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите цену товара:")
    await state.set_state(AddProduct.price)

# Хэндлер для получения цены товара
@admin_router_product_handler.message(AddProduct.price)
async def add_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await message.answer("Введите бренд товара:")
        await state.set_state(AddProduct.brand)
    except ValueError:
        await message.answer("Некорректная цена. Введите число.")

# Хэндлер для получения бренда товара
@admin_router_product_handler.message(AddProduct.brand)
async def add_product_brand(message: Message, state: FSMContext):
    await state.update_data(brand=message.text)
    await message.answer(
        "Отправьте до 20 изображений (по одному). Когда закончите, нажмите кнопку ниже:",
        reply_markup=done_keyboard
        )
    await state.set_state(AddProduct.images)

# Хэндлер для загрузки изображений товара
@admin_router_product_handler.message(AddProduct.images, F.content_type.in_({ContentType.PHOTO, ContentType.TEXT}))
async def add_product_images(message: Message, state: FSMContext):
    # Получаем текущее состояние данных
    data = await state.get_data()

    if "images" not in data:
        data["images"] = []

    if message.content_type == ContentType.PHOTO:
        if len(data["images"]) < 20:
            data["images"].append(message.photo[-1].file_id)
            await state.update_data(images=data["images"])  # Обновляем данные в FSM
            await message.answer(f"Добавлено изображение {len(data['images'])}/20")
        else:
            await message.answer("Максимум 20 изображений!")

    elif message.text == "✅ Завершить":
        await message.answer(f"Теперь добавим варианты товара. "
                             f"Если товар представлен в нескольких размерах, "
                             f"заполните ниже данные для каждого размера, сначала "
                             f"(размер, цвет, наценку, скидку, колличество) для первого, "
                             f"затем те же поля для второго размера и т.д. "
                             f"Для того же товара другого цвета лучше добавить "
                             f"другие фотографии и создать отдельные карточки товаров:)"
                             )
        await message.answer(
            f"Введите размер товара\n"
            f"(например, S, M, L, XL):\n"
            f"(или 42, 44, 46, 48):\n"
            )
        await state.set_state(AddProduct.variant_size)


# Получаем размер или 'Завершить добавление вариантов'
@admin_router_product_handler.message(AddProduct.variant_size)
async def handle_variant_size_or_finish(message: Message, state: FSMContext):
    """Начинает логику добавления вариантов размера и цвета одного
    и того же товара, а так же завершает добавление вариантов, перехватывая
    текст кнопки '✅ Завершить добавление вариантов'.

    Так же добавила логику предпросмотра перед сохранением.
    """
    if message.text == "✅ Завершить добавление вариантов":
        # завершаем
        data = await state.get_data()
        if "variants" not in data or not data["variants"]:
            await message.answer("Вы не добавили ни одного варианта.")
            return

        # Добавила предпросмотр перед сохранением
        await send_product_preview(data, message, message.bot)

        await state.set_state(AddProduct.confirm)
        return

    # иначе продолжаем добавление нового варианта
    size = message.text.strip()
    if not size:
        await message.answer("Размер не может быть пустым. Введите размер ещё раз:")
        return
    await state.update_data(size=size)
    await message.answer("Введите цвет товара (например, Красный, Синий, Чёрный):")
    await state.set_state(AddProduct.variant_color)

# Получаем цвет
@admin_router_product_handler.message(AddProduct.variant_color)
async def add_variant_color(message: Message, state: FSMContext):
    color = message.text.strip()
    await state.update_data(color=color)
    await message.answer(
        f"Введите наценку за вариант в числовом формате, "
        f"наценка в рублях, добавляется к текущей цене товара, "
        f"(например, 200):"
        )
    await state.set_state(AddProduct.variant_additional_price)

# Получаем наценку
@admin_router_product_handler.message(AddProduct.variant_additional_price)
async def add_variant_additional_price(message: Message, state: FSMContext):
    try:
        additional_price = float(message.text.strip())
        await state.update_data(additional_price=additional_price)
        await message.answer("Введите скидку в процентах от 0 до 100 (например, 10):")
        await state.set_state(AddProduct.variant_discount)
    except ValueError:
        await message.answer("Некорректный ввод. Введите числовое значение наценки:")

# Получаем скидку
@admin_router_product_handler.message(AddProduct.variant_discount)
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
@admin_router_product_handler.message(AddProduct.variant_stock)
async def add_variant_stock(message: Message, state: FSMContext):
    try:
        stock = int(message.text.strip())
        if stock < 0:
            raise ValueError

        data = await state.get_data()  # data — это словарь, который хранит все данные состояния FSM
        variants = data.get("variants", [])  # data.get("variants", []) просто вернёт значение или пустой список

        variants.append({
            "size": data["size"],
            "color": data["color"],
            "additional_price": data["additional_price"],
            "discount_percent": data["discount_percent"],
            "stock": stock,
        })

        await state.update_data(variants=variants)

        await message.answer(
            "✅ Вариант добавлен!\n\nВведите новый размер или нажмите кнопку ниже, чтобы завершить:",
            reply_markup=variant_done_keyboard
            )
        await state.set_state(AddProduct.variant_size)

    except ValueError:
        await message.answer("❌ Некорректный ввод. Введите целое положительное число для количества на складе:")


# Хэндлер для подтверждения и сохранения товара
@admin_router_product_handler.message(
        AddProduct.confirm,
        F.text.in_({"✅ Подтвердить сохранение товара", "❌ Отмена сохранения товара"})
        )
async def confirm_cancel_product(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "✅ Подтвердить сохранение товара":
        data = await state.get_data()  # работаем с fsm как со словарём, читаеми меняем данные

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

        # Проверка изображений, загрузка изображений, сохранение, получение пути к изобр.
        if "images" in data and data["images"]:
            for file_id in data["images"]:
                file = await message.bot.get_file(file_id)
                await orm_save_product_image(file, new_product.id, session, message.bot)

        # Проверяем варианты товара
        if "variants" in data and data["variants"]:
            for variant in data["variants"]:
                new_variant = ProductVariant(product_id=new_product.id, **variant)
                session.add(new_variant)

        await session.commit()
        await message.answer("✅ Товар добавлен!", reply_markup=product_menu)

        await state.clear()

    elif message.text == "❌ Отмена сохранения товара":
        await state.clear()
        await message.answer(
            "Добавление товара отменено.",
            reply_markup=product_menu)

    else: # защита от случайного ввода
        await message.answer("Пожалуйста, выберите действие с помощью кнопок ниже.")



@admin_router_product_handler.message(F.text == "Список товаров")
@admin_required
async def view_all_products(message: Message, session: AsyncSession):
    products = await orm_get_all_products(session)

    if not products:
        await message.answer("📦 Нет добавленных товаров в базе.")
        return

    # Группируем по категориям
    products_by_category = defaultdict(list)
    for product in products:
        category_name = product.category.name if product.category else "Без категории"
        products_by_category[category_name].append(product)

    # Вывод в чат информации
    for category, items in products_by_category.items():
        await message.answer(f"<b>📂 Категория: {category}</b>", parse_mode="HTML")

        for product in items:
            # Основная информация о товаре
            text = format_product_info(product)  # используем готовую ф-ию форматирования
            await message.answer(text, parse_mode="HTML")


@admin_router_product_handler.message(F.text == "Посмотреть все товары с вариантами")
@admin_required
async def view_all_products(message: Message, session: AsyncSession):
    products = await orm_get_all_products(session)

    if not products:
        await message.answer("📦 Нет добавленных товаров в базе.")
        return

    # Группируем по категориям
    products_by_category = defaultdict(list)
    for product in products:
        category_name = product.category.name if product.category else "Без категории"
        products_by_category[category_name].append(product)

    # Вывод в чат информации
    for category, items in products_by_category.items():
        await message.answer(f"<b>📂 Категория: {category}</b>", parse_mode="HTML")

        for product in items:
            # Основная информация о товаре
            text = format_product_info(product)  # используем готовую ф-ию форматирования
            await message.answer(text, parse_mode="HTML")

            # Варианты товара
            if product.variants:
                for i, variant in enumerate(product.variants, start=1):
                    variant_text = (
                        f"<b>Вариант {i}:</b>\n" + format_variant_info(variant, base_price=product.price)
                        )
                    await message.answer(variant_text, parse_mode="HTML")
            else:
                await message.answer("🧩 Нет вариантов для этого товара.")


class ViewProduct(StatesGroup):
    """Описывает состояния для просмотра товара из БД."""
    waiting_for_product_id = State()


@admin_router_product_handler.message(Command("view_product"))
@admin_router_product_handler.message(F.text == "Посмотреть товар")
@admin_required
async def add_product_start(message: Message, state: FSMContext):
    await message.answer("Введите ID товара для просмотра:")
    await state.set_state(ViewProduct.waiting_for_product_id)


@admin_router_product_handler.message(ViewProduct.waiting_for_product_id)
@admin_required
async def handle_view_product(message: Message, state: FSMContext, session: AsyncSession):
    # проверка введённых данных, должно быть число
    try:
        product_id = int(message.text)
    except ValueError:
        await message.answer("❌ Введите корректный числовой ID.")
        return

    # проверка, существует ли товар с таким ID
    product = await orm_get_product_by_id(session, product_id)
    if not product:
        await message.answer("❌ Товар с таким ID не найден.")
        return

    # Показываем основную информацию о товаре
    text = format_product_info(product)
    await message.answer("<b>Информация о товаре:</b>", parse_mode="HTML")
    await message.answer(text, parse_mode="HTML")

    # Отправляем одно фото, если есть
    if product.images:
        first_image = product.images[0]
        if first_image.image_url.startswith("AgAC"):
            await message.answer_photo(photo=first_image.image_url)
        else:
            path = os.path.join(UPLOAD_DIR, first_image.image_url)
            if os.path.exists(path):
                with open(path, "rb") as f:
                    await message.answer_photo(photo=f)

    # Показываем варианты
    if product.variants:
        await message.answer("<b>Варианты товара:</b>", parse_mode="HTML")
        for i, variant in enumerate(product.variants, start=1):
            text = f"<b>Вариант {i}:</b>\n" + format_variant_info(variant, base_price=product.price)
            await message.answer(text, parse_mode="HTML")
    else:
        await message.answer("— У товара нет вариантов.")

    await state.clear()


class EditProduct(StatesGroup):
    """Описывает состояния для изменения описания товара в БД."""
    waiting_for_product_id = State()
    choose_field = State()
    new_value = State()
    confirm = State()


@admin_router_product_handler.message(F.text == "Редактировать товар")
@admin_required
async def start_edit_product(message: Message, state: FSMContext):
    await message.answer("Введите ID товара, который хотите отредактировать:")
    await state.set_state(EditProduct.waiting_for_product_id)


@admin_router_product_handler.message(EditProduct.waiting_for_product_id)
@admin_required
async def get_product_for_editing(message: Message, state: FSMContext, session: AsyncSession):
    try:
        product_id = int(message.text)
    except ValueError:
        await message.answer("❌ Введите корректный числовой ID.")
        return

    product = await orm_get_product_by_id(session, product_id)
    if not product:
        await message.answer("❌ Товар с таким ID не найден.")
        return

    await state.update_data(product_id=product_id)
    await message.answer(
        "Что вы хотите изменить?\nВыберите одно из полей:\n\n"
        " category\n name\n description\n price\n brand",
        parse_mode="HTML"
    )
    await state.set_state(EditProduct.choose_field)


@admin_router_product_handler.message(EditProduct.choose_field)
@admin_required
async def choose_field_to_edit(message: Message, state: FSMContext):
    field = message.text.strip().lower()
    if field not in ["category", "name", "description", "price", "brand"]:
        await message.answer("❌ Недопустимое поле. Выберите из: category, name, description, price, brand")
        return

    await state.update_data(field_to_edit=field)
    await message.answer(f"Введите новое значение для поля <b>{field}</b>:", parse_mode="HTML")
    await state.set_state(EditProduct.new_value)


@admin_router_product_handler.message(EditProduct.new_value)
@admin_required
async def apply_field_change(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    field = data["field_to_edit"]
    product_id = data["product_id"]
    new_value = message.text.strip()

    product = await orm_get_product_by_id(session, product_id)
    if not product:
        await message.answer("❌ Не удалось найти товар. Попробуйте снова.")
        await state.clear()
        return

    # Обработка категории отдельно (по имени)
    if field == "category":
        category = await orm_get_category_by_name(session, category_name=new_value)
        if not category:
            await message.answer("❌ Категория не найдена. Убедитесь, что она существует.")
            return
        product.category_id = category.id
    elif field == "price":
        try:
            product.price = float(new_value)
        except ValueError:
            await message.answer("❌ Некорректная цена. Введите число.")
            return
    else:
        setattr(product, field, new_value)  # Установить значение new_value в атрибут field объекта product

    await session.commit()
    await message.answer("✅ Изменения успешно сохранены!", reply_markup=product_menu)
    await state.clear()


class EditVariant(StatesGroup):
    """Описывает состояния для изменения варианта товара в БД."""
    waiting_for_variant_number = State()
    waiting_for_field = State()
    waiting_for_new_value = State()
    waiting_for_final_value = State()


@admin_router_product_handler.message(F.text == "Редактировать вариант товара")
@admin_required
async def start_edit_variant(message: Message, state: FSMContext):
    await message.answer("Введите ID товара, у которого хотите отредактировать вариант:")
    await state.set_state(EditVariant.waiting_for_variant_number)


@admin_router_product_handler.message(EditVariant.waiting_for_variant_number)
@admin_required
async def select_variant_to_edit(message: Message, state: FSMContext, session: AsyncSession):
    try:
        product_id = int(message.text.strip())
    except ValueError:
        await message.answer("Введите корректный числовой ID товара.")
        return

    product = await orm_get_product_by_id(session, product_id)
    if not product:
        await message.answer("❌ Товар с таким ID не найден.")
        return

    if not product.variants:
        await message.answer("У товара нет вариантов.")
        return

    await state.update_data(product_id=product_id)

    text = "Выберите номер варианта для редактирования:\n"
    for i, variant in enumerate(product.variants, start=1):
        text += f"\n<b>Вариант {i}:</b>\n" + format_variant_info(variant, base_price=product.price) + "\n"

    await message.answer(text, parse_mode="HTML")
    await message.answer("Введите номер варианта:")
    await state.set_state(EditVariant.waiting_for_field)


@admin_router_product_handler.message(EditVariant.waiting_for_field)
@admin_required
async def choose_variant_field(message: Message, state: FSMContext, session: AsyncSession):
    try:
        variant_index = int(message.text.strip()) - 1
    except ValueError:
        await message.answer("Введите корректный номер варианта.")
        return

    data = await state.get_data()
    product = await orm_get_product_by_id(session, data["product_id"])
    variants = product.variants

    if variant_index < 0 or variant_index >= len(variants):
        await message.answer("Нет варианта с таким номером.")
        return

    await state.update_data(variant_index=variant_index)
    await message.answer(
        "Введите, что хотите изменить: size, color, additional_price, discount_percent, stock"
    )
    await state.set_state(EditVariant.waiting_for_new_value)


@admin_router_product_handler.message(EditVariant.waiting_for_new_value)
@admin_required
async def update_variant_field(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    product = await orm_get_product_by_id(session, data["product_id"])
    variant = product.variants[data["variant_index"]]

    text = message.text.strip()

    await message.answer("Введите новое значение:")
    await state.update_data(field_to_edit=text)
    await state.set_state(EditVariant.waiting_for_final_value)


@admin_router_product_handler.message(EditVariant.waiting_for_final_value)
@admin_required
async def save_updated_variant(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    field = data["field_to_edit"]
    value = message.text.strip()

    product = await orm_get_product_by_id(session, data["product_id"])
    variant = product.variants[data["variant_index"]]

    try:
        if field in ("additional_price", "discount_percent"):
            setattr(variant, field, float(value))  # Установить значение float(value) в атрибут field объекта variant
        elif field == "stock":
            setattr(variant, field, int(value))
        elif field in ("size", "color"):
            setattr(variant, field, value)
        else:
            await message.answer("Неверное поле.")
            return

        await session.commit()
        await message.answer("✅ Вариант товара успешно обновлён!", reply_markup=product_menu)
    except Exception as e:
        await message.answer(f"Ошибка при обновлении: {e}")

    await state.clear()


class DeleteProduct(StatesGroup):
    """Описывает состояния для удаления товара из БД."""
    waiting_for_product_id = State()


@admin_router_product_handler.message(F.text == "Удалить товар")
@admin_required
async def start_delete_product(message: Message, state: FSMContext):
    await message.answer("Введите ID товара, который хотите удалить:")
    await state.set_state(DeleteProduct.waiting_for_product_id)


@admin_router_product_handler.message(DeleteProduct.waiting_for_product_id)
@admin_required
async def handle_delete_product(message: Message, state: FSMContext, session: AsyncSession):
    try:
        product_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректный числовой ID товара.")
        return

    product = await orm_get_product_by_id(session, product_id)
    if not product:
        await message.answer("❌ Товар с таким ID не найден.")
        await state.clear()
        return

    # Удаление изображений из файловой системы (фото хранились локально)
    for image in product.images:
        if not image.image_url.startswith("AgAC"):  # Telegram file_id обычно начинается с AgAC
            path = os.path.join(UPLOAD_DIR, image.image_url)
            if os.path.exists(path):
                os.remove(path)

    # Удаляем все связанные объекты (варианты и изображения)
    await orm_delete_product_images(session, product_id)
    await orm_delete_product_variants(session, product_id)
    await orm_delete_product(session, product)

    await session.commit()
    await message.answer("🗑 Товар и все связанные с ним данные удалены.", reply_markup=product_menu)
    await state.clear()
