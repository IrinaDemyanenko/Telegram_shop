from aiogram import types


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
