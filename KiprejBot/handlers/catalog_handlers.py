from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from keyboards.catalog_keyboards import get_category_inline_keyboard, get_pagination_keyboard
from utils.callback_data_filters import CategoryCallbackFactory
from database.orm_requests import orm_get_available_sizes, orm_get_filtered_products
from keyboards.catalog_keyboards import get_size_selection_inline_keyboard
from utils.product_card_formatter import format_product_card_text
from utils.pagination import custom_pagination


catalog_router = Router()


@catalog_router.message(F.text == "🏬 Каталог")
async def show_catalog(message: Message, session: AsyncSession):
    """Отображает категории каталога с кнопками."""
    keyboard = await get_category_inline_keyboard(session)
    await message.answer(
        "Добро пожаловать в магазин Kiprej!\n\nВыберите категорию товаров:",
        reply_markup=keyboard
    )

# обработчик нажатия на 'категорию' или 'все товары'
@catalog_router.callback_query(CategoryCallbackFactory.filter(F.action == 'size'))
async def show_size_options(
    callback: CallbackQuery,
    callback_data: CategoryCallbackFactory,
    session: AsyncSession
):
    """Pass"""
    category_id = callback_data.category_id
    sizes = await orm_get_available_sizes(session, category_id)

    keyboard = await get_size_selection_inline_keyboard(category_id, sizes)

    # ведём диалог с пользователем в этом же сообщении, меняем текст
    await callback.message.edit_text(
        text='Выберите нужный размер или нажмите "Показать всё"',
        reply_markup=keyboard
    )
    # закрываем часики, чтобы не подумали, что бот завис
    await callback.answer()


@catalog_router.callback_query(CategoryCallbackFactory.filter(F.action == 'show'))
async def show_filtered_products(
    callback: CallbackQuery,
    callback_data: CategoryCallbackFactory,
    session: AsyncSession
):
    """
    Показывает список товаров по выбранной категории и размеру.
    """
    category_id = callback_data.category_id
    selected_size = callback_data.size
    page = callback_data.page

    # Получаем все отфильтрованные товары
    products = await orm_get_filtered_products(session, category_id, selected_size)

    if not products:
        await callback.answer("Нет товаров по выбранным параметрам.", show_alert=True)
        return

    # Показываем только одну страницу с 10 товарами
    products_on_page = custom_pagination(products, page=page, page_size=10)

    if not products_on_page:
        await callback.answer("На этой странице нет товаров.", show_alert=True)
        return

    # Показываем первый товар (или все, если хочешь постранично)
    for product in products_on_page:
        images = product.images
        if not images:
            continue  # можно также показать заглушку "Нет фото"

        # Выбираем первую картинку
        image = images[0].file_path

        # Получаем первый подходящий вариант (по размеру) Если пользователь нажал "Показать всё", и размер не выбран (size == ''), то ты можешь не находить variant, а просто передавать None в format_product_card_text
        variant = next((v for v in product.variants if v.size == selected_size), None) if selected_size else None

        # Формируем текст и кнопки
        caption = format_product_card_text(
            product, variant, image_index=0, total_images=len(images)
            )
        keyboard = get_product_card_keyboard(product.id, total_images=len(images))

        await callback.message.answer_photo(
            photo=image,
            caption=caption,
            parse_mode='HTML',
            reply_markup=keyboard
        )

    # Показываем клавиатуру пагинации (т е кнопки вперёд-назад)
    pagination_keyboard = get_pagination_keyboard(category_id, selected_size, page)

    await callback.message.answer(
        text='Страница:',
        reply_markup=pagination_keyboard
    )

    await callback.answer()
