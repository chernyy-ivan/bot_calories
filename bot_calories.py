import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

import database

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

database.init_db()

# Состояния FSM для анкеты
class ProfileStates(StatesGroup):
    waiting_for_age = State()
    waiting_for_height = State()
    waiting_for_weight = State()
    waiting_for_target_weight = State()
    waiting_for_months = State()

# Состояния для дневника воды
class WaterStates(StatesGroup):
    waiting_for_custom_water = State()

# Состояния для логирования еды
class FoodStates(StatesGroup):
    waiting_for_calories = State()


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def check_water_limit(current_water: int, water_goal: int) -> str:
    """Проверяет превышение нормы воды и выдает текст-предупреждение"""
    if current_water > water_goal:
        return (
            "\n\n⚠️ *Внимание:* Ты превысил свою дневную норму! "
            "Пить слишком много воды не стоит — это создает лишнюю экстренную нагрузку на почки и вымывает минералы. "
            "Все хорошо в меру, старайся держаться ближе к рассчитанной норме! 🙌"
        )
    return f"\n\nОсталось выпить: {max(0, water_goal - current_water)} мл."


# --- КЛАВИАТУРЫ ---

def get_main_menu_keyboard():
    """Главное меню с раздельными вкладками дневника"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👤 Мой профиль", callback_data="view_profile"))
    builder.row(
        types.InlineKeyboardButton(text="💧 Дневник Воды", callback_data="menu_water"),
        types.InlineKeyboardButton(text="🍎 Дневник Еды", callback_data="menu_food")
    )
    builder.row(types.InlineKeyboardButton(text="⚙️ Перезаполнить анкету", callback_data="restart_survey"))
    return builder.as_markup()

def get_water_keyboard():
    """Клавиатура для быстрой вставки воды + свой ввод"""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="➕ 250 мл", callback_data="add_water_250"),
        types.InlineKeyboardButton(text="➕ 500 мл", callback_data="add_water_500")
    )
    builder.row(types.InlineKeyboardButton(text="✍️ Свой объём", callback_data="add_water_custom"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()

def get_food_keyboard():
    """Клавиатура для дневника еды"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✍️ Записать калории", callback_data="add_food_prompt"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()

def get_back_to_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()


# --- ХЕНДЛЕРЫ КОМАНД ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = database.get_user_profile(message.from_user.id)
    if user:
        await message.answer(
            f"Привет, {message.from_user.first_name}! Рад возвращению. 👋\n"
            "Твой профиль уже настроен. Используй меню для управления целями.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(
            f"Привет, {message.from_user.first_name}! 👋\n"
            "Я помогу тебе контролировать калории, воду и шаги.\n\n"
            "Давай настроим твой профиль. Сколько тебе лет? (Введи число)"
        )
        await state.set_state(ProfileStates.waiting_for_age)

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    await state.clear()
    user = database.get_user_profile(message.from_user.id)
    if not user:
        await message.answer("Сначала необходимо настроить профиль! Напиши /start")
        return
    await message.answer("📋 Главное меню:", reply_markup=get_main_menu_keyboard())


# --- ОБРАБОТКА НАЖАТИЙ НА КНОПКИ (CALLBACK_QUERY) ---

@dp.callback_query(F.data == "view_profile")
async def callback_view_profile(callback: types.CallbackQuery):
    user = database.get_user_profile(callback.from_user.id)
    if not user:
        await callback.message.edit_text("Профиль не найден. Пройди анкетирование через /start")
        await callback.answer()
        return

    weight_diff = user['current_weight'] - user['target_weight']
    if weight_diff > 0:
        goal_status = f"📉 Похудение (сбросить {round(weight_diff, 1)} кг за {user['target_months']} мес.)"
    elif weight_diff < 0:
        goal_status = f"📈 Набор массы (набрать {round(abs(weight_diff), 1)} кг за {user['target_months']} мес.)"
    else:
        goal_status = "⚖️ Поддержание веса"

    profile_text = (
        "👤 *Твой профиль и цели:*\n\n"
        f"• Возраст: {user['age']} лет\n"
        f"• Рост: {user['height']} см\n"
        f"• Текущий вес: {user['current_weight']} кг\n"
        f"• Целевой вес: {user['target_weight']} кг\n"
        f"• Направление: {goal_status}\n\n"
        f"🔥 *Норма калорий:* {user['calorie_goal']} ккал\n"
        f"💧 *Норма воды:* {user['water_goal']} мл"
    )
    await callback.message.edit_text(profile_text, parse_mode="Markdown", reply_markup=get_back_to_menu_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("📋 Главное меню:", reply_markup=get_main_menu_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "restart_survey")
async def callback_restart_survey(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Запускаем настройку заново. Сколько тебе лет?")
    await state.set_state(ProfileStates.waiting_for_age)
    await callback.message.delete()
    await callback.answer()


# --- ДНЕВНИК ВОДЫ ---

@dp.callback_query(F.data == "menu_water")
async def callback_menu_water(callback: types.CallbackQuery):
    user = database.get_user_profile(callback.from_user.id)
    log = database.get_or_create_daily_log(callback.from_user.id)
    
    status_text = check_water_limit(log['water_ml'], user['water_goal'])
    
    text = (
        "💧 *Дневник воды за сегодня:*\n\n"
        f"• Выпито: {log['water_ml']} мл\n"
        f"• Твоя норма: {user['water_goal']} мл"
        f"{status_text}"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_water_keyboard())
    await callback.answer()

# ИСПРАВЛЕНО: Теперь ловим только те кнопки, где в конце строки идут цифры веса (250, 500 и т.д.)
@dp.callback_query(F.data.startswith("add_water_") & F.data.split("_")[2].cast(str).isdigit())
async def callback_add_water(callback: types.CallbackQuery):
    amount = int(callback.data.split("_")[2])
    database.add_water_to_db(callback.from_user.id, amount)
    
    user = database.get_user_profile(callback.from_user.id)
    log = database.get_or_create_daily_log(callback.from_user.id)
    
    status_text = check_water_limit(log['water_ml'], user['water_goal'])
    
    text = (
        "💧 *Дневник воды за сегодня:*\n\n"
        f"• Выпито: {log['water_ml']} мл\n"
        f"• Твоя норма: {user['water_goal']} мл"
        f"{status_text}"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_water_keyboard())
    await callback.answer(f"Добавлено {amount} мл! 🥤")

@dp.callback_query(F.data == "add_water_custom")
async def callback_add_water_custom(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите количество выпитой воды в миллилитрах (мл):")
    await state.set_state(WaterStates.waiting_for_custom_water)
    await callback.message.delete()
    await callback.answer()

@dp.message(WaterStates.waiting_for_custom_water)
async def process_custom_water(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи количество миллилитров числом (например: 350)!")
        return
        
    amount = int(message.text)
    if amount <= 0:
        await message.answer("Объем должен быть больше нуля!")
        return
        
    database.add_water_to_db(message.from_user.id, amount)
    await message.answer(f"✅ Успешно записано: {amount} мл воды.")
    await message.answer("📋 Главное меню:", reply_markup=get_main_menu_keyboard())
    await state.clear()


# --- ДНЕВНИК ЕДЫ ---

@dp.callback_query(F.data == "menu_food")
async def callback_menu_food(callback: types.CallbackQuery):
    user = database.get_user_profile(callback.from_user.id)
    log = database.get_or_create_daily_log(callback.from_user.id)
    
    text = (
        "🍎 *Дневник еды за сегодня:*\n\n"
        f"• Съедено калорий: {log['calories_consumed']} ккал\n"
        f"• Твоя целевая норма: {user['calorie_goal']} ккал\n\n"
        f"Осталось ккал на сегодня: {max(0, user['calorie_goal'] - log['calories_consumed'])} ккал."
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_food_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "add_food_prompt")
async def callback_add_food_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите количество калорий (ккал), которые вы съели:")
    await state.set_state(FoodStates.waiting_for_calories)
    await callback.message.delete()
    await callback.answer()

@dp.message(FoodStates.waiting_for_calories)
async def process_food_calories(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи количество калорий числом!")
        return
        
    calories = int(message.text)
    database.add_calories_to_db(message.from_user.id, calories)
    
    await message.answer(f"✅ Успешно записано: {calories} ккал.")
    await message.answer("📋 Главное меню:", reply_markup=get_main_menu_keyboard())
    await state.clear()


# --- ПРОЦЕСС АНКЕТИРОВАНИЯ (FSM) ---

@dp.message(ProfileStates.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи возраст числом!")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Отлично! Теперь введи свой рост в сантиметрах:")
    await state.set_state(ProfileStates.waiting_for_height)

@dp.message(ProfileStates.waiting_for_height)
async def process_height(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи рост числом!")
        return
    await state.update_data(height=int(message.text))
    await message.answer("Введи свой текущий вес в кг:")
    await state.set_state(ProfileStates.waiting_for_weight)

@dp.message(ProfileStates.waiting_for_weight)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введи вес числом!")
        return
    await state.update_data(current_weight=weight)
    await message.answer("Каков твой целевой вес?:")
    await state.set_state(ProfileStates.waiting_for_target_weight)

@dp.message(ProfileStates.waiting_for_target_weight)
async def process_target_weight(message: types.Message, state: FSMContext):
    try:
        target_weight = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введи вес числом!")
        return
    await state.update_data(target_weight=target_weight)
    await message.answer("За сколько месяцев ты хочешь достичь цели?:")
    await state.set_state(ProfileStates.waiting_for_months)

@dp.message(ProfileStates.waiting_for_months)
async def process_target_months(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи количество месяцев числом!")
        return
        
    target_months = int(message.text)
    if target_months <= 0:
        await message.answer("Срок должен быть больше нуля!")
        return

    user_data = await state.get_data()
    age = user_data['age']
    height = user_data['height']
    current_weight = user_data['current_weight']
    target_weight = user_data['target_weight']
    
    water_goal = int(current_weight * 30)
    bmr = (10 * current_weight) + (6.25 * height) - (5 * age) + 5
    weight_diff = current_weight - target_weight
    
    if weight_diff > 0:
        kg_per_month = weight_diff / target_months
        if kg_per_month > 4:
            calorie_goal = int(bmr * 0.8)
        else:
            calorie_goal = int(bmr * 0.9)
    elif weight_diff < 0:
        calorie_goal = int(bmr * 1.1)
    else:
        calorie_goal = int(bmr)

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
    
    await message.answer(
        "🎉 *Профиль успешно настроен и сохранен!*\n\n"
        f"💧 *Норма воды:* {water_goal} мл в день.\n"
        f"🔥 *Расчетная норма калорий:* {calorie_goal} ккал.\n\n"
        "Открываю главное меню...",
        reply_markup=get_main_menu_keyboard()
    )
    await state.clear()


async def main():
    print("Бот успешно запущен и обновлен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")