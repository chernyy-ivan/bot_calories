from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import database
import keyboards
from states import ProfileStates

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = database.get_user_profile(message.from_user.id)
    if user:
        await message.answer(
            f"Привет, {message.from_user.first_name}! Рад возвращению. 👋\nТвой профиль настроен.",
            reply_markup=keyboards.get_main_menu_keyboard()
        )
    else:
        await message.answer(f"Привет! 👋 Давай настроим твой профиль. Сколько тебе лет?")
        await state.set_state(ProfileStates.waiting_for_age)

@router.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    await state.clear()
    user = database.get_user_profile(message.from_user.id)
    if not user:
        await message.answer("Сначала настройте профиль! Напишите /start")
        return
    await message.answer("📋 Главное меню:", reply_markup=keyboards.get_main_menu_keyboard())

@router.callback_query(F.data == "view_profile")
async def callback_view_profile(callback: types.CallbackQuery):
    user = database.get_user_profile(callback.from_user.id)
    
    # ЗАЩИТА: Если профиля нет в новой БД
    if not user:
        await callback.message.edit_text(
            "⚠️ Профиль не найден. Пожалуйста, пройди анкетирование заново через команду /start", 
            reply_markup=keyboards.get_back_to_menu_keyboard()
        )
        await callback.answer()
        return

    weight_diff = user['current_weight'] - user['target_weight']
    goal_status = "📉 Похудение" if weight_diff > 0 else "📈 Набор массы" if weight_diff < 0 else "⚖️ Поддержание"
    
    profile_text = (
        f"👤 *Профиль:*\n• Возраст: {user['age']}\n• Рост: {user['height']} см\n"
        f"• Вес: {user['current_weight']} кг\n• Цель: {user['target_weight']} кг ({goal_status})\n\n"
        f"🔥 *Норма калорий:* {user['calorie_goal']} ккал\n💧 *Норма воды:* {user['water_goal']} мл"
    )
    await callback.message.edit_text(profile_text, parse_mode="Markdown", reply_markup=keyboards.get_back_to_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("📋 Главное меню:", reply_markup=keyboards.get_main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "restart_survey")
async def callback_restart_survey(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Запускаем настройку заново. Сколько тебе лет?")
    await state.set_state(ProfileStates.waiting_for_age)
    await callback.message.delete()
    await callback.answer()

# --- FSM АНКЕТЫ ---
@router.message(ProfileStates.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введи число!")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Твой рост в см:")
    await state.set_state(ProfileStates.waiting_for_height)

@router.message(ProfileStates.waiting_for_height)
async def process_height(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введи число!")
        return
    await state.update_data(height=int(message.text))
    await message.answer("Твой текущий вес в кг:")
    await state.set_state(ProfileStates.waiting_for_weight)

@router.message(ProfileStates.waiting_for_weight)
async def process_weight(message: types.Message, state: FSMContext):
    try: weight = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Введи число!")
        return
    await state.update_data(current_weight=weight)
    await message.answer("Желаемый вес в конце похудения:")
    await state.set_state(ProfileStates.waiting_for_target_weight)

@router.message(ProfileStates.waiting_for_target_weight)
async def process_target_weight(message: types.Message, state: FSMContext):
    try: target_weight = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Введи число!")
        return
    await state.update_data(target_weight=target_weight)
    await message.answer("За сколько месяцев хочешь достичь цели?:")
    await state.set_state(ProfileStates.waiting_for_months)

@router.message(ProfileStates.waiting_for_months)
async def process_target_months(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введи число!")
        return
    target_months = int(message.text)
    
    user_data = await state.get_data()
    age, height, current_weight, target_weight = user_data['age'], user_data['height'], user_data['current_weight'], user_data['target_weight']
    
    water_goal = int(current_weight * 30)
    bmr = (10 * current_weight) + (6.25 * height) - (5 * age) + 5
    weight_diff = current_weight - target_weight
    calorie_goal = int(bmr * 0.8) if weight_diff > 0 else int(bmr * 1.1) if weight_diff < 0 else int(bmr)

    database.update_user_profile(message.from_user.id, message.from_user.username, age, height, current_weight, target_weight, target_months, calorie_goal, water_goal)
    await message.answer("🎉 Профиль сохранен!", reply_markup=keyboards.get_main_menu_keyboard())
    await state.clear()