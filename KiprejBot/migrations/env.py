import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import pool
from alembic import context
from database.db import Base  # Импортируем базу моделей
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем URL БД из .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Настройка логирования Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Создаём асинхронный движок
connectable = async_engine_from_config(
    {"sqlalchemy.url": DATABASE_URL},
    prefix="sqlalchemy.",
    poolclass=pool.NullPool,
    future=True,
)

# Функция для миграций
async def run_migrations():
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()

# Запуск асинхронных миграций
asyncio.run(run_migrations())
