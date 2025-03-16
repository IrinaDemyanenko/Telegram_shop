from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_category_keyboard(categories):
    """Создаёт клавиатуру с категориями товаров."""
    buttons = [KeyboardButton(c.name) for c in categories]
    return ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)

admin_menu = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton("Добавить товар")],
        [KeyboardButton("Удалить товар")],
        [KeyboardButton("Редактировать товар")],
        [KeyboardButton("Назад в главное меню")]
    ]
)
