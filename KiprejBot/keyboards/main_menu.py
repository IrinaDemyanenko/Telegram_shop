from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from utils.user_check import is_registered



# Главное меню с кнопками
def get_main_menu(is_admin=False):
    """Создаёт главное меню.

    - Если пользователь администратор → добавляет кнопку "🔧 Админ-меню".
    """

    keyboard = [
        [
            KeyboardButton(text="🏬 Каталог"),
            KeyboardButton(text="📞 Контакты")
        ],
        [
            KeyboardButton(text="🚚 Доставка и оплата"),
            KeyboardButton(text="👤 Профиль")
        ],
        [
            KeyboardButton(text="🛍 Мои заказы"),
            KeyboardButton(text="🏠 Мои адреса")
        ],
        [
            KeyboardButton(text="📝 Регистрация"),
        ],
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text="🔧 Админ-меню")])  # Добавляем кнопку для админов

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder='Добро пожаловать в Kiprej'
    )
