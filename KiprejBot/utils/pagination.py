from typing import Sequence, TypeVar

T = TypeVar("T")  # универсальный тип для любых объектов

def custom_pagination(items: Sequence[T], page: int = 1, page_size: int = 10) -> list[T]:
    """
    Возвращает элементы нужной страницы из общего списка.

    items: Список объектов (товары, заказы и т.д.)
    page: Номер страницы (начинается с 1)
    page_size: Количество элементов на одной странице
    return: Список объектов, входящих в заданную страницу

    Пример:
        items = [1, 2, 3, 4, 5, 6]
        paginate(items, page=2, page_size=2) => [3, 4]
    """
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]
