import re
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import update, delete
from utils.navigation import go_to_main_menu
from database.orm_requests import orm_delete_user, orm_register_user, orm_get_user_by_telegram, orm_update_user_profile
from database.db import async_session
from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from keyboards.user_keyboards import profile_menu
from keyboards.main_menu import get_main_menu
from utils.user_check import is_admin, is_registered, user_check



registration_router = Router()


# --- Регулярные выражения для валидации ---
EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
PHONE_REGEX = r"^\+?[0-9\-]{7,15}$"  # Пример: +1234567890 или 123-456-7890


def is_valid_full_name(full_name: str) -> bool:
    """Проверяет, что полное имя содержит хотя бы два слова."""
    return len(full_name.split()) >= 2

def is_valid_email(email: str) -> bool:
    """Проверяет корректность email по регулярному выражению."""
    return re.match(EMAIL_REGEX, email) is not None

def is_valid_phone(phone: str) -> bool:
    """Проверяет корректность номера телефона."""
    return re.match(PHONE_REGEX, phone) is not None

def get_field_value(input_value: str, current_value: str, validator=None) -> str:
    """
    Возвращает значение поля в зависимости от ввода пользователя.
      - Если введено ".", возвращает текущее значение.
      - Если введено "-", возвращает None.
      - Иначе проверяет валидатором (если задан) и возвращает input_value.
    """
    input_value = input_value.strip()
    if input_value == ".":
        return current_value
    if input_value == "-":
        return None
    if validator and not validator(input_value):
        return None
    return input_value


# Регистрация пользователя
class Registration(StatesGroup):
    """Хранит FSM состояния для создания профиля пользователя."""
    full_name = State()
    email = State()
    phone = State()


# @registration_router.message(Command("register"))
@registration_router.message(lambda message: message.text == "📝 Регистрация")
async def register_start(message: Message, state: FSMContext, session: AsyncSession):
    user = await user_check(session, message.from_user.id)
    if not user:
        await message.answer(
            "Добро пожаловать в магазин!\nПожалуйста, введите ваше полное имя:"
            )
        await state.set_state(Registration.full_name)
    else:
        await message.answer('Вы уже зарегистрированы.')

@registration_router.message(Registration.full_name)
async def process_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    if not is_valid_full_name(full_name):
        await message.answer(
            "Пожалуйста, введите корректное полное имя (имя и фамилию):"
            )
        return
    await state.update_data(full_name=full_name)
    await message.answer("Введите ваш email (если нет, введите '-' для пропуска):")
    await state.set_state(Registration.email)

@registration_router.message(Registration.email)
async def process_email(message: Message, state: FSMContext):
    email_input = message.text.strip()
    if email_input != "-" and not is_valid_email(email_input):
        await message.answer(
            "Пожалуйста, введите корректный email (например, example@gmail.com):"
            )
        return
    email = None if email_input == "-" else email_input
    await state.update_data(email=email)
    await message.answer("Введите ваш номер телефона (например, +1234567890):")
    await state.set_state(Registration.phone)

@registration_router.message(Registration.phone)
async def process_phone(message: Message, state: FSMContext, session: AsyncSession):
    phone_input = message.text.strip()
    if not is_valid_phone(phone_input):
        await message.answer(
            "Пожалуйста, введите корректный номер телефона (например, +1234567890):"
            )
        return
    phone = phone_input
    await state.update_data(phone=phone)
    user_data = await state.get_data()
    registration_data = {
        "telegram_id": message.from_user.id,
        "full_name": user_data.get("full_name"),
        "email": user_data.get("email"),
        "phone": user_data.get("phone")
    }
    # Извлекаем сессию из data (middleware предоставит ее из общего словаря)
    # session = data.get('session')
    # для быстрого выявления ошибок используем анотацию типов
    # session: AsyncSession = data["session"]
    await orm_register_user(session, registration_data)
    info = (
        "Регистрация завершена. Проверьте введённые данные:\n"
        f"Имя: {user_data.get('full_name')}\n"
        f"Email: {user_data.get('email') or 'не указан'}\n"
        f"Телефон: {user_data.get('phone')}"
    )
    await message.answer(info)
    await state.clear()


@registration_router.message(lambda message: message.text == "👤 Профиль")
async def profile_menu_handler(message: Message, session: AsyncSession):
    user = await user_check(session, message.from_user.id)
    if user:
        await message.answer(
            "Вы в разделе управления профилем. Выберите действие:",
            reply_markup=profile_menu
        )
    else:
        await message.answer(
            f'Вы не зарегистрированы. Чтобы попасть в раздел'
            f' управления профилем, пройдите, пожалуйста, регистрацию.'
            )

# Команда для просмотра профиля пользователя
# @registration_router.message(Command("my_profile"))
@registration_router.message(lambda message: message.text == '👓 Посмотреть профиль')
async def my_profile_handler(message: Message, session: AsyncSession):
    telegram_id = message.from_user.id
    user = await orm_get_user_by_telegram(session, telegram_id)
    if user:
        text = (
            f"Ваш профиль:\n"
            f"Имя: {user.full_name}\n"
            f"Email: {user.email or 'не указан'}\n"
            f"Телефон: {getattr(user, 'phone', 'не указан')}\n"
            f"Дата регистрации: {user.created_at.strftime('%d.%m.%Y') if user.created_at else 'не указано'}\n"
            f"TelegramID: {telegram_id}\n"
        )
        await message.answer(text)
    else:
        await message.answer(
            f"Пользователь не найден. Пожалуйста, зарегистрируйтесь, "
            f"используя команду /register"
            )


# Редактирование профиля
class EditProfile(StatesGroup):
    """Хранит FSM состояния для редактирования профиля пользователя."""
    current_user = State()  # Сохраняем изначальные данные пользователя
    full_name = State()
    email = State()
    phone = State()
    confirm = State()

# @registration_router.message(Command("edit_profile"))
@registration_router.message(lambda message: message.text == '✏️ Изменить профиль')
async def edit_profile_start(message: Message, state: FSMContext, session: AsyncSession):
    user = await orm_get_user_by_telegram(session, message.from_user.id)
    if not user:
        await message.answer(
            "Пользователь не найден. Зарегистрируйтесь с помощью /register."
            )
        return
    # Сохраняем текущие данные в состоянии для повторного использования
    await state.update_data(current_user={
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone
    })
    await message.answer(
        f"Редактирование профиля.\nВведите новое полное имя\n"
        f"(или ' . ' для сохранения текущего):"
    )
    await state.set_state(EditProfile.full_name)

@registration_router.message(EditProfile.full_name)
async def edit_full_name(message: Message, state: FSMContext):
    user_data = await state.get_data()
    current = user_data.get("current_user", {})
    new_full_name = get_field_value(
        message.text,
        current.get("full_name"),
        is_valid_full_name
        )
    if new_full_name is None:
        await message.answer(
            f"Пожалуйста, введите корректное полное имя\n "
            f"(например, Василий Иванов):"
            )
        return
    await state.update_data(full_name=new_full_name)
    await message.answer(
        f"Введите новый email\n"
        f"(или ' . ' для сохранения текущего,\n"
        f"' - ' для удаления текущего):"
        )
    await state.set_state(EditProfile.email)

@registration_router.message(EditProfile.email)
async def edit_email(message: Message, state: FSMContext):
    user_data = await state.get_data()
    current = user_data.get("current_user", {})
    new_email = get_field_value(
        message.text,
        current.get("email"),
        is_valid_email
        )
    await state.update_data(email=new_email)
    await message.answer(
        f"Введите новый номер телефона, например +79151231234\n "
        f"(или ' . ' для сохранения текущего):"
        )
    await state.set_state(EditProfile.phone)

@registration_router.message(EditProfile.phone)
async def edit_phone(message: Message, state: FSMContext, session: AsyncSession):
    user_data = await state.get_data()
    current = user_data.get("current_user", {})
    new_phone = get_field_value(
        message.text,
        current.get("phone"),
        is_valid_phone
        )
    await state.update_data(phone=new_phone)
    user_data = await state.get_data()
    info = (
        "Проверьте введённые данные:\n"
        f"Имя: {user_data.get('full_name')}\n"
        f"Email: {user_data.get('email') or 'не указан'}\n"
        f"Телефон: {user_data.get('phone')}\n\n"
        "Если все верно, отправьте 'Да'. Если хотите отменить изменения, отправьте любой символ."
    )
    await message.answer(info)
    await state.set_state(EditProfile.confirm)

@registration_router.message(EditProfile.confirm)
async def edit_confirm(message: Message, state: FSMContext, session: AsyncSession):
    confirmation = message.text.strip().lower()
    if confirmation == "да":
        user_data = await state.get_data()
        update_data = {
            "full_name": user_data.get("full_name"),
            "email": user_data.get("email"),
            "phone": user_data.get("phone")
        }
        await orm_update_user_profile(session, message.from_user.id, update_data)
        await message.answer("Ваш профиль успешно обновлен!")
    else:
        await message.answer("Редактирование профиля отменено.")
    await state.clear()

# Удаление профиля
class DeleteProfile(StatesGroup):
    """Хранит FSM состояния для удаления профиля пользователя."""

    confirm = State()


# @registration_router.message(Command("delete_profile"))
@registration_router.message(lambda message: message.text == '🗑 Удалить профиль')
async def delete_profile_handler(message: Message, state: FSMContext):
    await message.answer(
        f'Вы уверены, что хотите удалить свой аккаунт?\n'
        f'Введите "Удалить" для подтверждения или любой символ для отмены.'
        )
    await state.set_state(DeleteProfile.confirm)

@registration_router.message(DeleteProfile.confirm)
async def delete_profile_confirm(message: Message, state: FSMContext, session: AsyncSession):
    confirmation = message.text.strip().lower()
    if confirmation == "удалить":
        await orm_delete_user(session, message.from_user.id)
        await message.answer("Ваш аккаунт успешно удалён.")
    else:
        await message.answer("Удаление аккаунта отменено.")
    await state.clear()


@registration_router.message(F.text == "🔙 Назад в главное меню")
async def back_to_main_menu(message: Message, session: AsyncSession):
    await go_to_main_menu(message, session)
