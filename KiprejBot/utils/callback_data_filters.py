from aiogram.filters.callback_data import CallbackData


# создали фабрику callback_data
class CategoryCallbackFactory(CallbackData, prefix='catalog'):
    """Автоматически собирает callback_data по шаблону:

    "catalog" — префикс, просто чтобы отделять кнопки каталога от чужих
    "action" — что нужно сделать (например, size, show)
    "category_id" — id категории (может быть None для "все товары")
    "size" — выбранный размер (или "all")
    "page" - номер страницы

    Пример: catalog:show:3:all:2
    (action='show', category_id=3, size='all', page=2)
    """

    action: str
    category_id: int
    size: str
    page: int = 1


# Фабрика для всех действий, связанных с карточкой товара
class ProductCardCallbackFactory(CallbackData, prefix='product'):
    """Собирает callback_data по шаблону для карточки товара.

    'product' - префикс
    'action' - определяет действие, которое выполняется пользователем,
               так мы можем понять, какое действие нужно выполнить в
               обработчике:
        photo: Листание фотографии товара
        size: Выбор размера товара
        quantity: Изменение количества товара
        add: Добавление товара в корзину
    'product_id' - каждый callback связан с конкретным товаром
    'image_index' - это индекс изображения товара, мы предполагаем,
                    что товар может иметь несколько изображений, и
                    с помощью этого поля можно управлять перелистыванием
                    фото
    'size' - передаёт размер товара, если пользователь его выбрал, если
             нет, оно будет пустым ("")
    'quantity' - это количество товара, которое пользователь хочет
                 заказать, значение по умолчанию == 1
    """
    action: str  # photo, size, quantity, add
    product_id: int
    image_index: int = 0  # для листания фото
    size: str = ''
    quantity: int = 1
