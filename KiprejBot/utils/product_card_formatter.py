from database.models import Product, ProductVariant


def format_product_card_text(
        product: Product,
        variant: ProductVariant | None,
        image_index: int,
        total_images: int) -> str:
    """Форматирует текст для карточки товара в HTML-разметке."""

    # Рассчитываем цену с наценкой и скидкой для варианта
    price_text = f"{variant.get_final_price()} ₽"  # итоговая цена с наценкой и скидкой

    # Если есть старая цена (до скидки), добавляем её в текст
    old_price = variant.old_price()
    if old_price:
        price_text += f" <s>{old_price} ₽</s>"

    # Формируем текст для карточки товара
    text = f"""
Фото {image_index + 1}/{total_images}
<b>{product.name}</b>
<i>{product.description or 'Без описания'}</i>

Бренд: {product.brand or '—'}
Размер: {variant.size if variant else '—'}
Цвет: {variant.color if variant else '—'}

Цена: {price_text}
В наличии: {variant.stock if variant else 0} шт.
"""
    return text

# <b> — жирный текст (для важных данных)
# <s> — зачёркнутый текст (для старой цены)
# <i> — курсив (например, "Без описания")
# <br> — перенос строки, когда нужен, но нельзя использовать \n
