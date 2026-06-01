import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Инициализируем бота и диспетчер (главный роутер запросов)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Я твой бот-трекер калорий, воды и шагов.\n"
        "Скоро мы настроим твой профиль и начнем вести учет!"
    )

# Обработчик любого текстового сообщения (эхо-бот)
@dp.message()
async def echo_message(message: types.Message):
    await message.answer(f"Ты написал: {message.text}")

# Главная функция запуска
async def main():
    print("Бот успешно запущен и вышел на связь...")
    # Запускаем Long Polling — бесконечный опрос серверов Телеграма
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")