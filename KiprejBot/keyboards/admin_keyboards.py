from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_category_keyboard(categories):
    """Создаёт клавиатуру с категориями товаров."""
    buttons = [KeyboardButton(c.name) for c in categories]
    return ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)


admin_main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📂 Управление категориями")],
        [KeyboardButton(text="📦 Управление товарами")],
        [KeyboardButton(text="ℹ️ Список админ-команд")],
        [KeyboardButton(text="🔙 Выйти в главное меню")],
    ],
    resize_keyboard=True
)

product_menu = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text="Добавить товар")],
        [KeyboardButton(text="Посмотреть товар")],
        [KeyboardButton(text="Редактировать товар")],
        [KeyboardButton(text="Удалить товар")],
        [KeyboardButton(text="Назад в админ-меню")]
    ]
)


category_menu = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text="Добавить категорию")],
        [KeyboardButton(text="Посмотреть все категории")],
        [KeyboardButton(text="Редактировать категорию")],
        [KeyboardButton(text="Удалить категорию")],
        [KeyboardButton(text="Назад в админ-меню")]
    ]
)
