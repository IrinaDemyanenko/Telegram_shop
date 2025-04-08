from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Product


async def is_valid_integer(message: types.Message, field_name: str = "ID") -> int | None:
    """
    Проверяет, является ли message.text корректным целым числом.
    Возвращает число, если всё ок, иначе отправляет сообщение об ошибке
    и возвращает None.
    """
    if not message.text.isdigit():
        await message.answer(f"❌ Пожалуйста, введите корректный числовой {field_name}.")
        return None
    return int(message.text)


async def product_exists(session: AsyncSession, product_id: int) -> bool:
    """
    Проверяет, существует ли товар в БД по его ID.
    Возвращает True, если существует, иначе отправляет False.
    """
    result = await session.get(Product, product_id)
    return result is not None
    # is not None — это проверка: есть ли в result что-то или он пустой (None)
