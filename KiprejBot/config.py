import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ENV_ALLOWED_SUPERUSER_ID = int(os.getenv("ALLOWED_SUPERUSER_ID"))
