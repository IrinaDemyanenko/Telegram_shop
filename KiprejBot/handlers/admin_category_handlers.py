from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.fsm.state import State, StatesGroup
from database.models import Category, Product
from utils.navigation import go_to_admin_menu
from utils.role_decorator import admin_required
from utils.validation import is_valid_integer
from keyboards.admin_keyboards import admin_main_menu, category_menu
from database.orm_requests import (
    orm_add_category,
    orm_get_all_categories,
    orm_get_category_by_id,
    orm_update_category,
    orm_delete_category,
    category_has_products
)



admin_category_router = Router()



# Возврат в главное меню
@admin_category_router.message(F.text == "Выйти в админ-меню")
@admin_category_router.message(F.text == "Назад в админ-меню")
@admin_required
async def back_to_admin_menu(message: Message, session: AsyncSession):
    await go_to_admin_menu(message, session)


class CategoryStates(StatesGroup):
    waiting_for_category_name = State()
    waiting_for_category_description = State()
    waiting_for_category_id_for_edit = State()
    waiting_for_new_category_name = State()
    waiting_for_new_category_description = State()
    waiting_for_category_id_for_delete = State()


# ===== Добавить категорию =====
@admin_category_router.message(F.text == "Добавить категорию")
@admin_required
async def add_category_start(message: Message, state: FSMContext):
    await message.answer("Введите название новой категории:")
    await state.set_state(CategoryStates.waiting_for_category_name)


@admin_category_router.message(CategoryStates.waiting_for_category_name)
async def add_category_name_received(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание категории (или '-' если не нужно):")
    await state.set_state(CategoryStates.waiting_for_category_description)


@admin_category_router.message(CategoryStates.waiting_for_category_description)
async def add_category_description_received(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    name = data['name']
    description = None if message.text.strip() == '-' else message.text.strip()

    await orm_add_category(session, name=name, description=description)
    await message.answer(f"✅ Категория «{name}» успешно добавлена.", reply_markup=category_menu)
    await state.clear()


# ===== Посмотреть категории =====
@admin_category_router.message(F.text == "Посмотреть все категории")
@admin_required
async def view_categories(message: Message, session: AsyncSession):
    categories = await orm_get_all_categories(session)
    if not categories:
        await message.answer("Нет доступных категорий.")
    else:
        text = "\n".join([f"{c.id}. {c.name} — {c.description or 'Без описания'}" for c in categories])
        await message.answer(f"📂 Список категорий:\n{text}")


# ===== Редактировать категорию =====
@admin_category_router.message(F.text == "Редактировать категорию")
@admin_required
async def edit_category_start(message: Message, state: FSMContext):
    await message.answer("Введите ID категории, которую хотите отредактировать:")
    await state.set_state(CategoryStates.waiting_for_category_id_for_edit)


@admin_category_router.message(CategoryStates.waiting_for_category_id_for_edit)
async def edit_category_id_received(message: Message, state: FSMContext, session: AsyncSession):
    # проверка, что ввели число
    category_id = await is_valid_integer(message, "ID")

    if category_id is None:
        return

    # проверка, чтотакая категория существует
    category = await orm_get_category_by_id(session, category_id)
    if not category:
        await message.answer("❌ Категория с таким ID не найдена. Попробуйте снова:")
        return

    await state.update_data(category_id=category_id)
    await message.answer("Введите новое название категории:")
    await state.set_state(CategoryStates.waiting_for_new_category_name)


@admin_category_router.message(CategoryStates.waiting_for_new_category_name)
async def edit_category_new_name(message: Message, state: FSMContext):
    await state.update_data(new_name=message.text)
    await message.answer("Введите новое описание категории (или '-' если не нужно):")
    await state.set_state(CategoryStates.waiting_for_new_category_description)


@admin_category_router.message(CategoryStates.waiting_for_new_category_description)
async def edit_category_new_description(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    category_id = data['category_id']
    new_name = data['new_name']
    new_description = None if message.text.strip() == '-' else message.text.strip()

    await orm_update_category(session, category_id, new_name, new_description)
    await message.answer(f"✏️ Категория обновлена: {new_name}", reply_markup=category_menu)
    await state.clear()


# ===== Удалить категорию =====
@admin_category_router.message(F.text == "Удалить категорию")
@admin_required
async def delete_category_start(message: Message, state: FSMContext):
    await message.answer("Введите ID категории для удаления:")
    await state.set_state(CategoryStates.waiting_for_category_id_for_delete)


@admin_category_router.message(CategoryStates.waiting_for_category_id_for_delete)
async def delete_category_confirm(message: Message, state: FSMContext, session: AsyncSession):
    # проверка, что ввели число
    category_id = await is_valid_integer(message, "ID")

    if category_id is None:
        return

    # проверка, что такая категория существует
    category = await orm_get_category_by_id(session, category_id)
    if not category:
        await message.answer("❌ Категория с таким ID не найдена. Попробуйте снова:")
        return

    # проверка, есть ли товары в этой категории
    if await category_has_products(session, category_id):
        await message.answer(f"⚠️ У категории есть связанные товары."
                             f"Удалите или перенесите их перед удалением категории.")
        return

    deleted = await orm_delete_category(session, category_id)
    if deleted:
        await message.answer("✅ Категория удалена.", reply_markup=category_menu)
    else:
        await message.answer("⚠️ Категория не найдена или связана с товарами. Удаление невозможно.")
    await state.clear()
