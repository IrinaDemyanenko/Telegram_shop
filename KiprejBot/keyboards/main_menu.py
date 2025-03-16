from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Главное меню с кнопками
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🏬 Каталог"),
            KeyboardButton(text="📞 Контакты")
        ],
        [
            KeyboardButton(text="🚚 Доставка и оплата"),
            KeyboardButton(text="📝 Регистрация")
        ],
        [
            KeyboardButton(text="🛍 Мои заказы"),
            KeyboardButton(text="🏠 Мои адреса")
        ],
        [
            KeyboardButton(text="👤 Профиль"),
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder='Добро пожаловать в Kiprej'
)
