import aiofiles, hashlib
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Category, Review, User, Product, ProductImage, Cart, CartItem, Order, Address
from pathlib import Path

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
async def orm_get_category_by_name(session: AsyncSession, category_name: str):
    """Возвращает категорию по её названию."""
    query = select(Category).where(Category.name == category_name)
    result = await session.execute(query)
    return result.scalar()

async def orm_get_all_categories(session: AsyncSession):
    """Возвращает список всех категорий."""
    query = select(Category)
    result = await session.execute(query)
    return result.scalars().all()

# === Работа с товарами ===
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
    query = select(Product)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_product_by_id(session: AsyncSession, product_id: int):
    query = select(Product).where(Product.id == product_id)
    return await session.scalar(query)


# === Работа с изображениями товаров ===
UPLOAD_DIR = Path("static/uploads/products")

async def save_product_image(file, product_id: int, db: AsyncSession) -> str:
    """Асинхронно сохраняет изображение в файловой системе и записывает путь в БД

    file: объект файла, загруженный пользователем;
    product_id: ID товара, которому принадлежит изображение;
    db: сессия БД (AsyncSession), через которую мы будем записывать данные;
    Возвращает:
    str: строку с путём сохранённого файла.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Создаём папку, если её нет

    file_ext = file.filename.split(".")[:1]  # получаем расширение файла (jpg, png и т. д.)
    hashed_filename = hashlib.md5(file.filename.encode()).hexdigest()  # Генерируем уникальное имя
    filename = f"{product_id}_{hashed_filename}.{file_ext}"
    file_path = UPLOAD_DIR / filename  # Полный путь к изображению

    # Сохраняем файл на сервер
    try:
        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(await file.read())  # Асинхронно записываем файл

        # Записываем в БД
        new_image = ProductImage(product_id=product_id, image_url=str(file_path))
        db.add(new_image)
        await db.commit()

        return str(file_path)

    except Exception as e:
        print(f"Ошибка сохранения файла: {e}")
        return None


# === Работа с категориями ===
async def category_has_products(session: AsyncSession, category_id: int) -> bool:
    """Проверяет, есть ли у категории привязанные товары."""
    result = await session.execute(
        select(Product).where(Product.category_id == category_id)
    )
    return result.scalars().first() is not None

async def orm_get_all_categories(session: AsyncSession):
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

async def orm_add_item_to_cart(session: AsyncSession, cart: Cart, product_id: int, quantity: int = 1) -> None:
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

async def orm_remove_item_from_cart(session: AsyncSession, cart_item_id: int) -> None:
    stmt = delete(CartItem).where(CartItem.id == cart_item_id)
    await session.execute(stmt)
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
