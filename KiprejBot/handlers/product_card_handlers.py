from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import (CallbackQuery, InlineKeyboardMarkup,
                           InlineKeyboardButton, InputMediaPhoto)
from utils.callback_data_filters import ProductCardCallbackFactory
from database.orm_requests import (orm_get_product_with_images,
                                   orm_get_available_sizes_for_product,
                                   orm_add_product_to_cart
                                   )
from keyboards.product_card_keyboards import (
    get_quantity_keyboard,
    get_size_keyboard,
    get_photo_navigation_keyboard
)

product_card_router = Router()


# Обработчик: product:photo — листание фотографий
@product_card_router.callback_query(ProductCardCallbackFactory.filter(F.action == 'photo'))
async def change_product_photo(callback: CallbackQuery, callback_data: ProductCardCallbackFactory, session: AsyncSession):
    """Перелистывание фото товара в карточке товара."""

    product_id = callback_data.product_id
    image_index = callback_data.image_index

    # Получаем товар с фотографиями из БД
    product, images = await orm_get_product_with_images(product_id, session)

    if not images:
        await callback.answer(f'Нет изображений товара.')
        return

    # Корректируем индекс, чтобы листать по кругу
    image_index = image_index % len(image_index)

    # Получаем текущее фото
    current_photo = images[image_index].file_path

    keyboard = await get_photo_navigation_keyboard((product_id, image_index, images))

    # Редактируем фото в том же сообщении
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=current_photo,
            caption=f'<b>{product.name}</b>\n\n{product.description}',
            parse_mode='HTML'
        ),
        reply_markup=keyboard
    )

    await callback.answer()


# Обработчик: product:size — выбор размера
@product_card_router.callback_query(ProductCardCallbackFactory.filter(F.action == 'size'))
async def choose_size(callback: CallbackQuery, callback_data: ProductCardCallbackFactory, session: AsyncSession):
    """Выбор размера из доступных."""

    product_id = callback_data.product_id

    # Получаем список доступных размеров товара
    sizes = await orm_get_available_sizes_for_product(product_id, session)

    # Генерируем кнопки размеров списковым включением
    # При нажатии на конкретный размер, мы переходим на следующий этап — выбор
    # количества. То есть действие меняется на quantity
    keyboard = await get_size_keyboard(product_id, sizes)

    # edit_reply_markup() - поменять кнопки и оставить текст нетронутым
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(f'Выберите размер')


# Обработчик: product:quantity — изменение количества
@product_card_router.callback_query(ProductCardCallbackFactory.filter(F.action == 'quantity'))
async def choose_quantity(callback: CallbackQuery, callback_data: ProductCardCallbackFactory):
    """Указание количества товара для добавления в корзину."""
    # достаём переданные параметры из кнопки
    product_id = callback_data.product_id
    size = callback_data.size
    quantity = callback_data.quantity

    keyboard = await get_quantity_keyboard(product_id, size, quantity)

    # Меняем только inline-кнопки у текущего сообщения, не трогаем текст
    await callback.message.edit_reply_markup(reply_markup=keyboard)

    #  Показываем всплывающую подсказку пользователю после нажатия кнопки
    await callback.answer('Укажите количество')


# Обработчик: product:add — добавление в корзину
@product_card_router.callback_query(ProductCardCallbackFactory.filter(F.action == 'add'))
async def add_to_card(callback: CallbackQuery, callback_data: ProductCardCallbackFactory, session: AsyncSession):
    """Добавление товара в корзину."""

    user_id = callback.from_user.id
    product_id = callback_data.product_id
    size = callback_data.size
    quantity = callback_data.quantity

    # Добавляем в корзину (функцию напишем позже)
    await orm_add_product_to_cart(user_id, product_id, size, quantity, session)

    await callback.answer('Добавлено в корзину 🛒', show_alert=True)


@product_card_router.callback_query(F.data == 'noop')
async def noop_handler(callback: CallbackQuery):
    await callback.answer()
