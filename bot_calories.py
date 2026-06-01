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


# --- КЛАВИАТУРЫ ---

def get_main_menu_keyboard():
    """Создает инлайн-клавиатуру главного меню"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👤 Мой профиль", callback_data="view_profile"))
    builder.row(types.InlineKeyboardButton(text="📊 Дневник (Скоро)", callback_data="coming_soon"))
    builder.row(types.InlineKeyboardButton(text="⚙️ Перезаполнить анкету", callback_data="restart_survey"))
    return builder.as_markup()

def get_back_to_menu_keyboard():
    """Создает кнопку возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()


# --- ХЕНДЛЕРЫ КОМАНД ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # Проверяем, есть ли уже пользователь в базе
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
    """Команда для вызова главного меню в любой момент"""
    await state.clear()  # Сбрасываем состояния, если пользователь ушел из анкеты
    user = database.get_user_profile(message.from_user.id)
    if not user:
        await message.answer("Сначала необходимо настроить профиль! Напиши /start")
        return
    await message.answer("📋 Главное меню:", reply_markup=get_main_menu_keyboard())


# --- ОБРАБОТКА НАЖАТИЙ НА КНОПКИ (CALLBACK_QUERY) ---

@dp.callback_query(F.data == "view_profile")
async def callback_view_profile(callback: types.CallbackQuery):
    """Просмотр данных профиля"""
    user = database.get_user_profile(callback.from_user.id)
    
    if not user:
        await callback.message.edit_text("Профиль не найден. Пожалуйста, пройдите анкетирование через /start")
        await callback.answer()
        return

    # Определяем тип цели для красивого вывода
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
    
    # Редактируем старое сообщение вместо отправки нового, чтобы не спамить чат
    await callback.message.edit_text(profile_text, parse_mode="Markdown", reply_markup=get_back_to_menu_keyboard())
    # Обязательно уведомляем Telegram, что кнопка обработана
    await callback.answer()

@dp.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: types.CallbackQuery):
    """Возврат в главное меню из любого подраздела"""
    await callback.message.edit_text("📋 Главное меню:", reply_markup=get_main_menu_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "restart_survey")
async def callback_restart_survey(callback: types.CallbackQuery, state: FSMContext):
    """Запуск анкеты заново прямо из меню"""
    await state.clear()
    await callback.message.answer("Запускаем настройку заново. Сколько тебе лет?")
    await state.set_state(ProfileStates.waiting_for_age)
    # Удаляем сообщение с меню, чтобы пользователь переключился на анкету
    await callback.message.delete()
    await callback.answer()

@dp.callback_query(F.data == "coming_soon")
async def callback_coming_soon(callback: types.CallbackQuery):
    """Временная заглушка для функций в разработке"""
    await callback.answer("Эта функция будет добавлена в следующих уроках! 🚀", show_alert=True)


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