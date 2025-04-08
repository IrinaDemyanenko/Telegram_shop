from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Category
from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_requests import orm_get_all_categories
from utils.callback_data_filters import CategoryCallbackFactory


async def get_category_inline_keyboard(session: AsyncSession) -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру с категориями и кнопкой 'Все товары'."""
    categories = await orm_get_all_categories(session)

    buttons = [
        [InlineKeyboardButton(text='Все товары', callback_data='catalog_all')],
    ]
    for category in categories:
        buttons.append([
            InlineKeyboardButton(
                text=category.name,
                callback_data=f'catalog_category_{category.id}'
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_size_selection_inline_keyboard(category_id: int, sizes: list[str]) -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру с размерами и кнопкой 'Показать всё'."""
    keyboard = []

    # для каждого размера добавляем кнопку
    for size in sizes:
        keyboard.append([
            InlineKeyboardButton(
                text=f'Размер: {size}',
                callback_data=CategoryCallbackFactory(
                    action='show',
                    category_id=category_id,
                    size=size
                ).pack()  # генерируем callback_data по шаблону
            )
        ])

    # В конец клавиатуры добавим кнопку показать все размеры
    keyboard.append([
        InlineKeyboardButton(
            text='Показать всё',
            callback_data=CategoryCallbackFactory(
                action='show',
                category_id=None,  # не указываем категории, показать все
                size=''  # без определённого размера
            ).pack()
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_pagination_keyboard(category_id: int | None, size: str, page: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру с кнопками пагинации: 'Назад' и 'Вперёд'."""
    buttons = []

    # Кнопка "Назад" (только если страница > 1)
    if page > 1:
        buttons.append(
            InlineKeyboardButton(
                text='⬅️ Назад',
                callback_data=CategoryCallbackFactory(
                    action='show',
                    category_id=category_id,
                    size=size,
                    page=page - 1
                ).pack()
            )
        )
    # Кнопка "Вперёд"
    buttons.append(
        InlineKeyboardButton(
            text='Вперёд ➡️',
            callback_data=CategoryCallbackFactory(
                action='show',
                category_id=category_id,
                size=size,
                page=page + 1
            ).pack()
        )
    )
    return InlineKeyboardMarkup(inline_keyboard=[buttons])
