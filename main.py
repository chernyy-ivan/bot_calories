import asyncio
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

import database
# Импортируем сборный рутер из папки handlers
from handlers import router as main_router

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализируем БД
database.init_db()

# Подключаем наш большой общий рутер обработчиков
dp.include_router(main_router)

async def main():
    print("Бот успешно запущен в модульной архитектуре...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")