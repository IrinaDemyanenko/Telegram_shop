from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Клавиатура управления профилем
profile_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✏️ Изменить профиль"),
            KeyboardButton(text="🗑 Удалить профиль")
        ],
        [
            KeyboardButton(text="👓 Посмотреть профиль"),
            KeyboardButton(text="🔙 Назад в главное меню")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие с профилем"
)
