import logging
from sqlalchemy import func, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Product, ProductView

async def log_product_view(session: AsyncSession, product_id: int, user_id: int = None):
    """
    Логирует просмотр товара.
    :param session: объект AsyncSession
    :param product_id: id товара
    :param user_id: id пользователя (опционально)
    """
    view = ProductView(product_id=product_id, user_id=user_id)
    session.add(view)
    await session.commit()

async def get_popular_products(session: AsyncSession, limit: int = 5):
    """
    Возвращает список популярных товаров по количеству просмотров.
    :param session: объект AsyncSession
    :param limit: сколько топовых товаров вернуть (по умолчанию 5)
    :return: список кортежей (Product, view_count)
    """
    query = (
        select(Product, func.count(ProductView.id).label("view_count"))
        .join(ProductView, Product.id == ProductView.product_id)
        .group_by(Product.id)
        .order_by(desc("view_count"))
        .limit(limit)
    )
    result = await session.execute(query)
    popular = result.all()  # Список кортежей (Product, view_count)
    return popular
