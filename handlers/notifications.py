import asyncio
from aiogram import Bot
import database

async def send_water_reminder(bot: Bot):
    while True:
        # Интервал 2 часа (7200 секунд)
        await asyncio.sleep(7200)
        
        conn = database.sqlite3.connect(database.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        conn.close()
        
        for user in users:
            user_id = user[0]
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text="💧 *Пора попить воды!* \nНе забывай поддерживать водный баланс в течение дня.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Не удалось отправить сообщение {user_id}: {e}")