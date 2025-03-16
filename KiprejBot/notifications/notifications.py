import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from database.db import async_session
from database.models import User, Order
from database.orm_requests import orm_get_orders_for_user


async def send_order_status_notifications(bot: Bot):
    """
    Рассылает уведомления о статусе заказов.
    Для каждого заказа, у которого установлен shipping_status, отправляется уведомление пользователю.
    """
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.shipping_status.isnot(None)))
        orders = result.scalars().all()
        for order in orders:
            result_user = await session.execute(select(User).where(User.id == order.user_id))
            user = result_user.scalar()
            if user:
                try:
                    await bot.send_message(
                        user.telegram_id,
                        f"Ваш заказ #{order.id} обновлён:\nСтатус: {order.shipping_status}"
                    )
                except Exception as e:
                    print(f"Ошибка отправки уведомления пользователю {user.telegram_id}: {e}")

async def send_promotions_notifications(bot: Bot):
    """
    Рассылка уведомлений о новинках и акциях магазина.
    Отправляет сообщение только тем пользователям, которые подписаны на рассылку.
    Добавлена базовая персонализация: если у пользователя есть заказы, отправляем персонализированное сообщение.
    """
    async with async_session() as session:
        # Выбираем пользователей, подписанных на рассылку
        result = await session.execute(select(User).where(User.is_subscribed == True))
        users = result.scalars().all()

    for user in users:
        # Персонализируем сообщение на основе истории заказов
        async with async_session() as session:
            orders = await orm_get_orders_for_user(session, user)
        if orders:
            message_text = (
                f"{user.full_name}, для вас подготовлены эксклюзивные предложения!\n"
                "Скидки до 25% на новые коллекции одежды и аксессуаров. Спешите!"
            )
        else:
            message_text = (
                "Новые поступления и акции в нашем магазине!\n"
                "Скидки до 20% на новую коллекцию. Проверьте новинки!"
            )
        try:
            await bot.send_message(user.telegram_id, message_text)
        except Exception as e:
            print(f"Ошибка отправки уведомления пользователю {user.telegram_id}: {e}")

async def send_notifications(bot: Bot):
    """
    Основная функция для рассылки уведомлений:
    - Отправляет уведомления о статусе заказов.
    - Рассылает промо-уведомления с персонализацией.
    """
    await send_order_status_notifications(bot)
    await send_promotions_notifications(bot)
