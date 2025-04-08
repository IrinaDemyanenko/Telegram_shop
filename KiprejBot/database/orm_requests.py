from typing import Optional
import aiofiles, hashlib
from uuid import uuid4
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Category, Review, User, Product, ProductImage, Cart, CartItem, Order, Address, ProductVariant
from pathlib import Path
from config import UPLOAD_DIR
from sqlalchemy.orm import selectinload

# === Работа с пользователями ===
async def orm_register_user(session: AsyncSession, data: dict) -> None:
    """Регистрирует нового пользователя."""
    user = User(
        telegram_id=data["telegram_id"],
        full_name=data["full_name"],
        email=data.get("email"),  # data.get() тк необязательный параметр
        phone=data["phone"]
    )
    session.add(user)
    await session.commit()

async def orm_get_user_by_telegram(session: AsyncSession, telegram_id: int):
    query = select(User).where(User.telegram_id == telegram_id)
    return await session.scalar(query)

async def orm_update_user_profile(session: AsyncSession, telegram_id: int, update_data: dict) -> None:
    """
    Обновляет профиль пользователя по telegram_id.
    update_data: словарь с новыми значениями полей (например, full_name, email, phone)
    """
    query = update(User).where(User.telegram_id == telegram_id).values(**update_data)
    await session.execute(query)
    await session.commit()

async def orm_delete_user(session: AsyncSession, telegram_id: int) -> None:
    """
    Удаляет пользователя по telegram_id.
    """
    query = delete(User).where(User.telegram_id == telegram_id)
    await session.execute(query)
    await session.commit()


async def orm_get_user_role(session: AsyncSession, telegram_id: int) -> str:
    """
    Получает роль пользователя по его telegram_id.
    Возвращает строку с ролью ('user', 'admin', 'superuser') или 'user' по умолчанию.
    """
    query = select(User.role).where(User.telegram_id == telegram_id)
    result = await session.execute(query)
    role = result.scalar()

    print(f"🎭 Роль пользователя {telegram_id}: {role}")  # Добавляем отладку

    return role if role else "user"  # Если роли нет, считаем, что это обычный пользователь

# === Работа с категориями ===
# Базовый запрос со связями
def get_base_product_query():
    """Все товары со своими изображениями и со своими вариантами, отсортированные по id."""
    return select(Product).options(
        selectinload(Product.images),
        selectinload(Product.variants)
    ).order_by(Product.id)


# Фильтрация по категории
def apply_category_filter(query, category_id: Optional[int]):
    """Применить к любому запросу фильтр по категории товара."""
    if category_id is not None:
        query = query.where(Product.category_id == category_id)
    return query


# Фильтрация по размеру (наличие нужного варианта)
def apply_size_filter(query, size: Optional[str]):
    """Применить к запросу фильтр по размеру товара."""
    if size:
        query = query.where(
            exists().where(
                (ProductVariant.product_id == Product.id) &
                (ProductVariant.size == size)
            )
        )
    return query

async def orm_get_category_by_name(session: AsyncSession, category_name: str):
    """Возвращает категорию по её названию."""
    query = select(Category).where(Category.name == category_name)
    result = await session.execute(query)
    return result.scalar()

async def orm_get_all_categories(session: AsyncSession) -> list[Category]:
    """Возвращает список всех категорий товаров."""
    query = select(Category).order_by(Category.name)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_filtered_products(
    session: AsyncSession,
    category_id: Optional[int] = None,
    size: Optional[str] = None
) -> list[Product]:
    """Список товаров, отфильтрованных по категории и размеру."""
    query = get_base_product_query()
    query = apply_category_filter(query, category_id)
    query = apply_size_filter(query, size)

    result = await session.execute(query)
    return result.scalars().all()

# === Работа с товарами и с вариантами ===
async def orm_add_product(session: AsyncSession, data: dict) -> Product:
    """Добавляет новый товар."""
    product = Product(
        name=data["name"],
        description=data.get("description"),
        price=data["price"]
    )
    session.add(product)
    await session.commit()
    return product

async def orm_get_all_products(session: AsyncSession):
    """Возвращает все товары с предзагруженными категориями и вариантами,
    отсортированные по ID.
    """
    query = select(Product).options(
        selectinload(Product.category),
        selectinload(Product.variants)
    ).order_by(Product.id)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_product_by_id(session: AsyncSession, product_id: int):
    """Возвращает товар по id."""
    query = (
        select(Product)
        .options(selectinload(Product.variants), selectinload(Product.images), selectinload(Product.category))
        .where(Product.id == product_id)
    )
    result = await session.execute(query)
    return result.scalars().first()

async def orm_get_all_products_with_variants(session):
    """Получаем все товары с категориями и вариантами.
    SQLAlchemy сделает:
    Один запрос, чтобы получить все продукты.
    Второй запрос, чтобы получить все варианты для этих продуктов.
    И сам «свяжет» их в Python.
    selectinload - выборочная загрузка.
    """
    query = select(Product).options(
        selectinload(Product.variants),
        selectinload(Product.category),
    )
    result = await session.execute(query)
    return result.scalars().all()

async def orm_delete_product_images(session, product_id):
    """Удаляет связанные с товаром изображения, принимает id товара."""
    query = delete(ProductImage).where(ProductImage.product_id == product_id)
    await session.execute(query)
    await session.commit()

async def orm_delete_product_variants(session, product_id):
    """Удаляет связанные с товаром варианты, принимает id товара."""
    query = delete(ProductVariant).where(ProductVariant.product_id == product_id)
    await session.execute(query)
    await session.commit()

async def orm_delete_product(session, product_id):
    """Удаляет товар, принимает id товара."""
    query = delete(Product).where(Product.id == product_id)
    await session.execute(query)
    await session.commit()

async def orm_get_available_sizes(session: AsyncSession, category_id: int) -> list[str]:
    """Получает список доступных размеров одежды в выбраной категории товаров."""
    query = (
        select(ProductVariant.size)
        .distinct()
        .join(Product)
        .where(ProductVariant.stock > 0)
    )
    if category_id is not None:
        query = query.where(Product.category_id == category_id)

    result = await session.execute(query)
    return [row[0] for row in result.all() if row[0]]

async def orm_get_available_sizes_for_product(product_id: int, session: AsyncSession):
    """Получает список всех доступныч размеров для конкретного
    товара, из таблицы вариантов товара, без дублей.
    """
    query = select(ProductVariant.size).where(ProductVariant.product_id == product_id).distinct()
    result = await session.execute(query)
    sizes = [row[0] for row in result.all() if row[0]]
    return sizes

async def orm_get_product_with_images(product_id: int, session: AsyncSession):
    """Получает товар со всеми изображениями (списком адресов изображений).
    product_id: int - id товара
    session: AsyncSession - подключение к БД
    """
    query = select(Product).where(Product.id == product_id).options(selectinload(Product.images))
    result = await session.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        return None, []
    return product, product.images

async def orm_get_product_variant_by_size(
        session: AsyncSession, product_id: int, size: str
) -> Optional[ProductVariant]:
    """Возвращает вариант товара по id товара и выбранному размеру.

    session: Асинхронная сессия SQLAlchemy.
    product_id: Идентификатор товара.
    size: Выбранный размер.
    return: Объект ProductVariant или None, если вариант не найден.
    """
    query = select(ProductVariant).where(
        ProductVariant.product_id == product_id,
        ProductVariant.size == size
        )
    result = await session.execute(query)
    variant = result.scalar()  # возвращает первую колонку в первом ряду
    return variant

# === Работа с изображениями товаров ===

async def orm_save_product_image(file, product_id: int, db: AsyncSession, bot=None) -> str:
    """Асинхронно сохраняет изображение в файловой системе и записывает путь в БД

    file: объект файла, загруженный пользователем через bot.get_file();
    product_id: ID товара, которому принадлежит изображение;
    db: сессия БД (AsyncSession), через которую мы будем записывать данные;
    bot: экземпляр бота для скачивания файла
    Возвращает путь к сохранённому файлу (str), либо None при ошибке.
    """
    if bot is None:
        raise ValueError("Bot instance must be provided for saving the image.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Создаём папку, если её нет

    # Получаем расширение файла
    file_ext = file.file_path.split(".")[-1]  # jpg, png и т.д.
    filename = f"{product_id}_{uuid4().hex}.{file_ext}"  # например '42_3fa85f6457174562b3fc2c963f66afa6.jpg'
    file_path = UPLOAD_DIR / filename

    try:
        # Скачиваем файл с серверов Telegram
        await bot.download_file(file.file_path, destination=file_path)

        # Сохраняем запись в БД
        new_image = ProductImage(product_id=product_id, image_url=str(file_path))
        db.add(new_image)
        await db.commit()

        return str(file_path)

    except Exception as e:
        print(f"Ошибка сохранения файла: {e}")
        return None

    # Улучшила функцию: save_product_image(file_id, ..., bot) — теперь она сама умеет:
    # получить файл по file_id;
    # узнать путь на серверах Telegram;
    # и сама скачать файл по file_path


# === Работа с категориями ===
async def orm_category_has_products(session: AsyncSession, category_id: int) -> bool:
    """Проверяет, есть ли у категории привязанные товары."""
    result = await session.execute(
        select(Product).where(Product.category_id == category_id)
    )
    return result.scalars().first() is not None

async def orm_orm_get_all_categories(session: AsyncSession):
    result = await session.execute(select(Category))
    return result.scalars().all()


async def orm_get_category_by_id(session: AsyncSession, category_id: int):
    """Проверяет, существует ли категория с указанным ID."""
    result = await session.execute(select(Category).where(Category.id == category_id))
    return result.scalar()


async def orm_add_category(session: AsyncSession, name: str, description: str = None):
    category = Category(name=name, description=description)
    session.add(category)
    await session.commit()
    return category


async def orm_update_category(session: AsyncSession, category_id: int, name: str, description: str = None):
    stmt = (
        update(Category)
        .where(Category.id == category_id)
        .values(name=name, description=description)
    )
    await session.execute(stmt)
    await session.commit()


async def orm_delete_category(session: AsyncSession, category_id: int):
    # Проверим, есть ли связанные товары
    result = await session.execute(select(Product).where(Product.category_id == category_id))
    linked_products = result.scalars().all()

    if linked_products:
        return False  # Нельзя удалить, если есть связанные товары
    # Ищем саму категорию
    category = await session.get(Category, category_id)
    if not category:
        return False

    await session.delete(category)
    await session.commit()
    return True

# === Работа с корзиной ===
async def orm_get_or_create_cart(session: AsyncSession, user: User):
    query = select(Cart).where(Cart.user_id == user.id)
    cart = await session.scalar(query)
    if not cart:
        cart = Cart(user_id=user.id)
        session.add(cart)
        await session.commit()
    return cart

async def orm_add_item_to_cart(
        session: AsyncSession,
        cart: Cart,
        product_id: int,
        quantity: int = 1
) -> None:
    query = select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    item = await session.scalar(query)
    if item:
        item.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        session.add(item)
    await session.commit()

async def orm_get_cart_items(session: AsyncSession, cart: Cart):
    query = select(CartItem).where(CartItem.cart_id == cart.id)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_cart_item(
        session: AsyncSession,
        cart_id: int,
        product_id: int,
        variant_id: int
) -> Optional[CartItem]:
    """Возвращает товар из корзины по id корзины, id товара и id варианта.

    session: Асинхронная сессия SQLAlchemy.
    cart_id: Идентификатор корзины.
    product_id: Идентификатор товара.
    variant_id: Идентификатор варианта товара.
    return: Объект CartItem или None, если элемент не найден.
    """
    query = select(CartItem).where(
        CartItem.cart_id == cart_id,
        CartItem.product_id == product_id,
        CartItem.variant_id == variant_id
    )
    result = session.execute(query)
    return result.scalar()

async def orm_remove_item_from_cart(session: AsyncSession, cart_item_id: int) -> None:
    stmt = delete(CartItem).where(CartItem.id == cart_item_id)
    await session.execute(stmt)
    await session.commit()

async def orm_add_product_to_cart(
    user_id: int,
    product_id: int,
    size: str,
    quantity: int,
    session: AsyncSession
) -> None:
    """
    Добавляет товар с выбранным размером в корзину пользователя.

    1. Получает пользователя по telegram_id (user_id).
    2. Получает или создаёт корзину для этого пользователя.
    3. Получает товар и вариант (по размеру) для выбранного товара.
    4. Если элемент уже есть в корзине – увеличивает количество,
       иначе – создаёт новый элемент корзины с ценой на момент добавления.
    """
    # 1. Получаем пользователя
    user = await orm_get_user_by_telegram(session, user_id)
    if not user:
        raise ValueError(f'Пользователь с telegram_id {user_id} не найден.')

     # 2. Получаем или создаём корзину для пользователя
    cart = await orm_get_or_create_cart(session, user)

    # 3. Получаем товар по id
    product = await orm_get_product_by_id(session, product_id)
    if not product:
        raise ValueError(f'Товар с id {product_id} не найден.')

    # 4. Получаем вариант товара с нужным размером
    variant = await orm_get_product_variant_by_size(session, product.id, size)
    if not variant:
        raise ValueError(f'Вариант товара с размером {size} для товара {product.name} не найден.')

    # 5.Рассчитываем цену на момент добавления
    price_at_time = variant.get_final_price()

    # 6. Проверяем, есть ли уже элемент корзины с этим товаром и вариантом,
    # если есть, увеличиваем колличество на quantity, если нет создаём новый CartItem
    cart_item = await orm_get_cart_item(session, cart.id, product.id, variant.id)
    if cart_item:
        cart_item.quantity += quantity
    else:
        new_item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            variant_id=variant.id,
            quantity=quantity,
            price_at_time=price_at_time
        )
        session.add(new_item)
    await session.commit()


# === Работа с заказами ===
async def orm_create_order(session: AsyncSession, user: User, total_amount: float) -> Order:
    order = Order(user_id=user.id, total_amount=total_amount)
    session.add(order)
    await session.commit()
    return order

async def orm_update_order_payment(session: AsyncSession, order_id: int, is_paid: bool, external_order_id: str = None) -> None:
    stmt = update(Order).where(Order.id == order_id).values(is_paid=is_paid, external_order_id=external_order_id)
    await session.execute(stmt)
    await session.commit()

async def orm_get_orders_for_user(session: AsyncSession, user: User):
    query = select(Order).where(Order.user_id == user.id)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_addresses_for_user(session: AsyncSession, user: User):
    """Возвращает список адресов доставки для данного пользователя."""
    query = select(Address).where(Address.user_id == user.id)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_create_review(session: AsyncSession, data: dict) -> Review:
    """
    Создает новый отзыв.
    Ожидается data: {
       "product_id": int,
       "user_id": int,
       "rating": int,          # Оценка от 1 до 5
       "comment": str (опционально)
    }
    """
    review = Review(
        product_id=data["product_id"],
        user_id=data["user_id"],
        rating=data["rating"],
        comment=data.get("comment")
    )
    session.add(review)
    await session.commit()
    return review

async def orm_get_reviews_for_product(session: AsyncSession, product_id: int):
    """
    Возвращает список отзывов для указанного товара.
    """
    query = select(Review).where(Review.product_id == product_id, Review.is_approved == True)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_approve_review(session: AsyncSession, review_id: int, is_approved: bool) -> None:
    """
    Обновляет статус модерации отзыва.
    """
    stmt = update(Review).where(Review.id == review_id).values(is_approved=is_approved)
    await session.execute(stmt)
    await session.commit()
