import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()  # Загружаем переменные из .env

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ENV_ALLOWED_SUPERUSER_ID = int(os.getenv("ALLOWED_SUPERUSER_ID"))

# Путь для изображений товаров
UPLOAD_DIR = Path("static/uploads/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Создание директории, если не существует
# Это безопасно: mkdir(..., exist_ok=True) не вызовет ошибку, если папка уже есть
