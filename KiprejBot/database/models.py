from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, func
from sqlalchemy import Enum
import enum


class Base(DeclarativeBase):
    pass

# -----------------------------
# Пользователь
# -----------------------------

# Создаём Enum для ролей
class RoleEnum(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERUSER = "superuser"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    # Добавляем поле подписки на рассылку
    is_subscribed: Mapped[bool] = mapped_column(Boolean, default=True)
    # Поле для роли пользователя, значения: user, admin, superuser
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.USER)

    # Связи
    cart = relationship("Cart", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")

# -----------------------------
# Категории товаров
# -----------------------------
class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    products = relationship("Product", back_populates="category")

# -----------------------------
# Товар
# -----------------------------
class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

    # Категория товара
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", back_populates="products")

    # Связь с изображениями
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    # Связь с вариантами (например, размер, цвет)
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    # Связь с отзывами
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    # Cвязь: просмотры товара
    views = relationship("ProductView", back_populates="product", cascade="all, delete-orphan")

# -----------------------------
# Изображения товара
# -----------------------------
class ProductImage(Base):
    __tablename__ = "product_images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)   # Локальный путь к файлу фото

    product = relationship("Product", back_populates="images")

# -----------------------------
# Варианты товара (например, размер, цвет)
# -----------------------------
class ProductVariant(Base):
    __tablename__ = "product_variants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    size: Mapped[str] = mapped_column(String(20), nullable=False)  # Размер (XS, S, M, L, XL)
    color: Mapped[str] = mapped_column(String(50), nullable=True)  # Цвет (если нужен)
    additional_price: Mapped[float] = mapped_column(Float, default=0.0)  # Наценка за вариант (руб.)
    discount_percent: Mapped[float] = mapped_column(Float, default=0.0)  # Скидка для этого варианта (%)
    stock: Mapped[int] = mapped_column(Integer, default=0)  # кол-во для конкретного варианта

    product = relationship("Product", back_populates="variants")

    def get_final_price(self) -> float:
        """Рассчитывает конечную цену варианта с учётом наценки и скидки.

        Возвращает итоговую цену варианта товара:
        - Базовая цена берётся из товара
        - Плюс наценка за размер/цвет (additional_price)
        - Минус скидка (discount_percent)
        """
        base_price = self.product.price + self.additional_price  # Основная цена + наценка

        if self.discount_percent > 0:
            final_price = base_price * (1 - self.discount_percent / 100)
        else:
            final_price = base_price

        return round(final_price, 2)  # Округляем цену до 2 знаков после запятой

    def old_price(self):
        """Возвращает "старую цену" (базовая цена + наценка за вариант)
        до применения скидки, если скидка есть. Чтобы подчеркнуть выгоду покупки.
        Используется для зачёркнутого текста в карточке товара.
        """
        if self.discount_percent > 0:
            return round(self.product.price + self.additional_price, 2)
        return None



# -----------------------------
# Корзина и элементы корзины
# -----------------------------
class Cart(Base):
    __tablename__ = "carts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

class CartItem(Base):
    __tablename__ = "cart_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id: Mapped[int] = mapped_column(Integer, ForeignKey("product_variants.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price_at_time: Mapped[float] = mapped_column(Float, nullable=False)  # цена на момент добавления

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")  # связать элемент корзины с конкретным вариантом товара

# -----------------------------
# Адрес доставки пользователя
# -----------------------------
class Address(Base):
    __tablename__ = "addresses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    address_line: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False)

    user = relationship("User", back_populates="addresses")

# -----------------------------
# Заказ и позиции заказа
# -----------------------------
class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

    external_order_id: Mapped[str] = mapped_column(String(100), nullable=True)  # для интеграции с платежными системами
    shipping_status: Mapped[str] = mapped_column(String(50), nullable=True)  # например: "в обработке", "отправлен"
    payment_method: Mapped[str] = mapped_column(String(50), nullable=True)   # например: "Яндекс.Касса", "Карта"
    shipping_address: Mapped[str] = mapped_column(String(255), nullable=True)  # может быть расширен через отдельную таблицу

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id: Mapped[int] = mapped_column(Integer, ForeignKey("product_variants.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[float] = mapped_column(Float, nullable=False)  # цена за единицу на момент заказа

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")


# -----------------------------
# Отзывы и рейтинг товаров
# -----------------------------
class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # оценка (например, от 1 до 5)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)  # статус модерации
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


# -----------------------------
# Модель для логирования просмотров товара
# -----------------------------
class ProductView(Base):
    __tablename__ = "product_views"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    # Если пользователь зарегистрирован, можно сохранить его id; иначе оставим NULL
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    view_time: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

    product = relationship("Product", back_populates="views")
