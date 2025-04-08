from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_category_keyboard(categories):
    """Создаёт клавиатуру с категориями товаров."""
    buttons = [[KeyboardButton(text=c.name)] for c in categories]
    # Если категории пусты — добавим заглушку
    if not buttons:
        buttons = [[KeyboardButton(text="Нет доступных категорий")]]

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )


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
        [KeyboardButton(text="Список товаров")],
        [KeyboardButton(text="Редактировать товар")],
        [KeyboardButton(text="Редактировать вариант товара")],
        [KeyboardButton(text="Удалить товар")],
        [KeyboardButton(text="Посмотреть все товары с вариантами")],
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


# Кнопка завершения действия
done_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ Завершить")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура для вариантов товара
variant_done_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ Завершить добавление вариантов")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура для подтверждения завершения добавления товара в БД
confirm_product_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Подтвердить сохранение товара")],
        [KeyboardButton(text="❌ Отмена сохранения товара")]
    ],
    resize_keyboard=True
)
