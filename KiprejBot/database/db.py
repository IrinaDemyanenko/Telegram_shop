import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Column, select
from sqlalchemy import func
from config import DATABASE_URL
from database.models import Base
import os
from dotenv import load_dotenv


# Загружаем переменные окружения из .env
load_dotenv()

# Берём URL БД из .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Создаём асинхронный движок PostgreSQL
engine = create_async_engine(DATABASE_URL, echo=True)

# Создаём фабрику сессий
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# Функция для создания таблиц, если их еще нет
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Функция для удаления таблиц (если понадобится)
async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
