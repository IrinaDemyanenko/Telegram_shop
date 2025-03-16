import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import BOT_TOKEN
from database.db import create_db, async_session
from database.db_middleware import DataBaseSession
from handlers.user_handlers import user_router
from handlers.admin_handlers import admin_router
from handlers.superuser_handlers import superuser_router
from notifications.notifications import send_notifications
from handlers.review_handlers import review_router
from handlers.registration_handlers import registration_router
from handlers.admin_product_handler import admin_router_product_management
from pathlib import Path


# Автоматическое создание папки для изображений
UPLOAD_DIR = Path("static/uploads/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

print(f"📂 Директория для загрузки изображений: {UPLOAD_DIR.resolve()}")


# Создаем объект бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализируем планировщик (если нужны задачи по расписанию)
scheduler = AsyncIOScheduler()

# Добавляем задачу для рассылки уведомлений каждый день в 18:00
scheduler.add_job(
    lambda: asyncio.create_task(send_notifications(bot)),
    CronTrigger(hour=18, minute=0, timezone="Europe/Moscow")
)

# Пример функции планировщика (можно расширять по необходимости)
async def scheduled_job():
    # Здесь можно добавить задачи, например, рассылку уведомлений
    await bot.send_message(chat_id=123456789, text="Это запланированное сообщение!")

# Добавляем задачу в планировщик (каждый день в 12:00)
scheduler.add_job(scheduled_job, CronTrigger(hour=12, minute=0, timezone="Europe/Moscow"))

# Устанавливаем команду "/menu" в кнопке с тремя полосками
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command='menu', description='Открыть главное меню')
    ]
    await bot.set_my_commands(commands)

async def main():
    """Запускает основной сценарий бота-магазина."""
    # Создаем таблицы, если их еще нет
    await create_db()

    # подключим db_middleware к основному роутеру, на самый ранний этап, но уже после прохождения всех фильтров
    dp.update.middleware(DataBaseSession(session_pool=async_session))
    # регистрируем второй мидлваре SchedulerMiddleware, тоже на все обновления
    #dp.update.middleware(SchedulerMiddleware(scheduler))

    # Регистрируем роутеры
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(superuser_router)
    dp.include_router(review_router)
    dp.include_router(registration_router)
    dp.include_router(admin_router_product_management)

    # Запускаем планировщик
    scheduler.start()

    # Устанавливаем команды (меню три полоски)
    await set_commands(bot)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
