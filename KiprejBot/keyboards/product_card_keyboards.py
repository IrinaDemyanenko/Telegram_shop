from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.callback_data_filters import ProductCardCallbackFactory


def get_photo_navigation_keyboard(product_id: int, image_index: int, images: int) -> InlineKeyboardMarkup:
    """Создаёт кнопки для перелистывания фото вперёд - назад."""
    # Создаём инлайн-кнопки "вперёд/назад"
    prev_index = (image_index - 1) % len(images)
    next_index = (image_index + 1) % len(images)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [  # Две кнопки рядом
            InlineKeyboardButton(
                text='⬅️',
                callback_data=ProductCardCallbackFactory(
                    action='photo',
                    product_id=product_id,
                    image_index=prev_index
                ).pack()
            ),
            InlineKeyboardButton(
                text='➡️',
                callback_data=ProductCardCallbackFactory(
                    action='photo',
                    product_id=product_id,
                    image_index=next_index
                ).pack()
            )
        ]
    ])

    return keyboard


def get_size_keyboard(product_id: int, sizes: list[str]) -> InlineKeyboardMarkup:
    """Генерирует кнопки доступных размеров вариантов."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            InlineKeyboardButton(
                text=size,
                callback_data=ProductCardCallbackFactory(
                    action='quantity',
                    product_id=product_id,
                    size=size,
                    quantity=1
                ).pack()
            )
            for size in sizes
        ]
    )
    return keyboard


def get_quantity_keyboard(product_id: int, size: str, quantity: int) -> InlineKeyboardMarkup:
    """Создаёт кнопки увеличения или уменьшения количества товара."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [  # Три кнопки в ряд
            InlineKeyboardButton(
                text='➖',
                callback_data=ProductCardCallbackFactory(
                    action='quantity',
                    product_id=product_id,
                    size=size,
                    quantity=max(1, quantity - 1)  # новый колбэк с уменьшенным количеством, но не меньше 1
                ).pack()
            ),
            InlineKeyboardButton(
                text=f'{quantity}',
                callback_data='noop'  # "заглушка", не предназначена для обработки
            ),
            InlineKeyboardButton(
                text='➕',
                callback_data=ProductCardCallbackFactory(
                    action='quantity',
                    product_id=product_id,
                    size=size,
                    quantity=quantity + 1  # на 1 больше текущего кол-ва
                ).pack()
            )
        ],
        [  # Ниже одна большая кнопка добавить
            InlineKeyboardButton(
                text='🛒 В корзину',
                callback_data=ProductCardCallbackFactory(
                    action='add',
                    product_id=product_id,
                    size=size,
                    quantity=quantity
                ).pack()
            )
        ]
    ])
    return keyboard
