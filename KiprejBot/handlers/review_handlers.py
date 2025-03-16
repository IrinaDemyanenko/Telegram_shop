from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import async_session
from database.orm_requests import orm_create_review, orm_get_reviews_for_product, orm_approve_review

review_router = Router()

@review_router.message(Command("create_review"))
async def create_review_handler(message: types.Message):
    """
    Создает отзыв.
    Ожидается формат:
    /create_review <product_id> <rating> <комментарий>
    Пример: /create_review 5 4 Отличный товар!
    """
    parts = message.text.split(maxsplit=3)
    if len(parts) < 3:
        await message.answer("Используйте: /create_review <product_id> <rating> <комментарий>")
        return
    try:
        product_id = int(parts[1])
        rating = int(parts[2])
        comment = parts[3] if len(parts) >= 4 else ""
        data = {
            "product_id": product_id,
            "user_id": message.from_user.id,  # Используем telegram_id; можно изменить на внутренний id, если нужно
            "rating": rating,
            "comment": comment
        }
        async with async_session() as session:
            review = await orm_create_review(session, data)
        await message.answer(f"Отзыв создан с id {review.id}. Он будет отображаться после модерации.")
    except Exception as e:
        await message.answer("Ошибка при создании отзыва.")

@review_router.message(Command("product_reviews"))
async def product_reviews_handler(message: types.Message):
    """
    Показывает отзывы для указанного товара.
    Ожидается: /product_reviews <product_id>
    """
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Используйте: /product_reviews <product_id>")
        return
    try:
        product_id = int(parts[1])
        async with async_session() as session:
            reviews = await orm_get_reviews_for_product(session, product_id)
        if reviews:
            text = f"Отзывы для товара {product_id}:\n"
            for review in reviews:
                text += f"ID: {review.id}, Оценка: {review.rating}, Комментарий: {review.comment}\n"
            await message.answer(text)
        else:
            await message.answer("Нет одобренных отзывов для этого товара.")
    except Exception as e:
        await message.answer("Ошибка при получении отзывов.")

@review_router.message(Command("approve_review"))
async def approve_review_handler(message: types.Message):
    """
    Обновляет статус отзыва.
    Ожидается: /approve_review <review_id> <yes/no>
    """
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Используйте: /approve_review <review_id> <yes/no>")
        return
    try:
        review_id = int(parts[1])
        is_approved = True if parts[2].lower() == "yes" else False
        async with async_session() as session:
            await orm_approve_review(session, review_id, is_approved)
        await message.answer(f"Отзыв {review_id} обновлен: одобрен = {is_approved}.")
    except Exception as e:
        await message.answer("Ошибка при обновлении отзыва.")
