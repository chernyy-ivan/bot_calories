import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

# Импортируем наш модуль для работы с базой данных
import database

# Загружаем токен из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализируем БД (создаем таблицы, если их нет)
database.init_db()

# Состояния машины состояний (FSM) для анкеты
class ProfileStates(StatesGroup):
    waiting_for_age = State()
    waiting_for_height = State()
    waiting_for_weight = State()
    waiting_for_target_weight = State()
    waiting_for_months = State()

# Команда /start — начало опроса
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Я помогу тебе контролировать калории, воду и шаги.\n\n"
        "Чтобы начать, давай настроим твой профиль. "
        "Сколько тебе лет? (Введи число)"
    )
    await state.set_state(ProfileStates.waiting_for_age)

# 1. Получаем возраст
@dp.message(ProfileStates.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи возраст числом!")
        return
        
    await state.update_data(age=int(message.text))
    await message.answer("Отлично! Теперь введи свой рост в сантиметрах (например, 180):")
    await state.set_state(ProfileStates.waiting_for_height)

# 2. Получаем рост
@dp.message(ProfileStates.waiting_for_height)
async def process_height(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи рост числом!")
        return
        
    await state.update_data(height=int(message.text))
    await message.answer("Введи свой текущий вес в кг (можно дробный, через точку или запятую, например 95.5):")
    await state.set_state(ProfileStates.waiting_for_weight)

# 3. Получаем текущий вес
@dp.message(ProfileStates.waiting_for_weight)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введи вес числом!")
        return
        
    await state.update_data(current_weight=weight)
    await message.answer("Каков твой целевой вес? (К какому результату стремишься):")
    await state.set_state(ProfileStates.waiting_for_target_weight)

# 4. Получаем целевой вес
@dp.message(ProfileStates.waiting_for_target_weight)
async def process_target_weight(message: types.Message, state: FSMContext):
    try:
        target_weight = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введи вес числом!")
        return
        
    await state.update_data(target_weight=target_weight)
    await message.answer("За сколько месяцев ты хочешь достичь этой цели? (Введи число месяцев, например: 3):")
    await state.set_state(ProfileStates.waiting_for_months)

# 5. Получаем срок, рассчитываем нормы и сохраняем профиль
@dp.message(ProfileStates.waiting_for_months)
async def process_target_months(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи количество месяцев числом!")
        return
        
    target_months = int(message.text)
    if target_months <= 0:
        await message.answer("Срок должен быть больше нуля!")
        return

    # Достаем все собранные данные из памяти FSM
    user_data = await state.get_data()
    age = user_data['age']
    height = user_data['height']
    current_weight = user_data['current_weight']
    target_weight = user_data['target_weight']
    
    # Считаем базовые нормы (формула Миффлина-Сан Жеора для мужчин)
    water_goal = int(current_weight * 30)  # 30 мл на 1 кг веса
    bmr = (10 * current_weight) + (6.25 * height) - (5 * age) + 5
    
    weight_diff = current_weight - target_weight
    
    # Расчет дефицита/профицита в зависимости от направления цели
    if weight_diff > 0:
        # Цель — похудение
        kg_per_month = weight_diff / target_months
        goal_text = (
            f"🎯 *Цель:* Похудение\n"
            f"• Сбросить: {round(weight_diff, 1)} кг\n"
            f"• Срок: {target_months} мес. (~{round(kg_per_month, 1)} кг в месяц)\n"
        )
        
        # Проверка на безопасную скорость похудения (не более 4 кг в месяц)
        if kg_per_month > 4:
            await message.answer("⚠️ *Внимание:* Сбрасывать больше 4 кг в месяц может быть вредно для здоровья. Я установил норму для безопасного темпа.")
            calorie_goal = int(bmr * 0.8)  # Максимальный дефицит 20%
        else:
            calorie_goal = int(bmr * 0.9)  # Комфортный дефицит 10%
            
    elif weight_diff < 0:
        # Цель — набор массы
        kg_to_gain = abs(weight_diff)
        goal_text = (
            f"🎯 *Цель:* Набор массы\n"
            f"• Набрать: {round(kg_to_gain, 1)} кг\n"
            f"• Срок: {target_months} мес. (~{round(kg_to_gain / target_months, 1)} кг в месяц)\n"
        )
        calorie_goal = int(bmr * 1.1)  # Профицит 10% для набора мышц
        
    else:
        # Цель — поддержание веса
        goal_text = (
            f"🎯 *Цель:* Поддержание текущего веса\n"
            f"• Текущий вес: {current_weight} кг\n"
        )
        calorie_goal = int(bmr)  # Калории поддержки

    # Записываем данные в базу SQLite
    database.update_user_profile(
        user_id=message.from_user.id,
        username=message.from_user.username,
        age=age,
        height=height,
        current_weight=current_weight,
        target_weight=target_weight,
        target_months=target_months,
        calorie_goal=calorie_goal,
        water_goal=water_goal
    )
    
    # Отправляем пользователю результат вычислений
    await message.answer(
        "🎉 *Профиль успешно настроен и сохранен!*\n\n"
        f"{goal_text}\n"
        f"💧 *Норма воды:* {water_goal} мл в день.\n"
        f"🔥 *Расчетная норма калорий:* {calorie_goal} ккал."
    )
    
    # Полностью очищаем состояние (завершаем анкету)
    await state.clear()

async def main():
    print("Бот успешно запущен и обновлен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")