from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
import database
import keyboards
from states import FoodStates

router = Router()

@router.callback_query(F.data == "menu_food")
async def callback_menu_food(callback: types.CallbackQuery):
    user = database.get_user_profile(callback.from_user.id)
    if not user:
        await callback.message.edit_text("⚠️ Сначала заполни анкету через /start", reply_markup=keyboards.get_back_to_menu_keyboard())
        await callback.answer()
        return

    log = database.get_or_create_daily_log(callback.from_user.id)
    text = f"🍎 *Дневник еды:*\n\n• Съедено: {log['calories_consumed']} ккал\n• Норма: {user['calorie_goal']} ккал\n\nОсталось: {max(0, user['calorie_goal'] - log['calories_consumed'])} ккал."
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboards.get_food_keyboard())
    await callback.answer()

@router.callback_query(F.data == "add_food_prompt")
async def callback_add_food_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📝 Что ты съел(а)? Напиши название:")
    await state.set_state(FoodStates.waiting_for_food_name)
    await callback.message.delete()
    await callback.answer()

@router.message(FoodStates.waiting_for_food_name)
async def process_food_name(message: types.Message, state: FSMContext):
    food_name = message.text.strip()
    await state.update_data(food_name=food_name)
    await message.answer(f"Сколько ккал в блюде «{food_name}»?")
    await state.set_state(FoodStates.waiting_for_calories)

@router.message(FoodStates.waiting_for_calories)
async def process_food_calories(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введи число!")
        return
    calories = int(message.text)
    database.add_calories_to_db(message.from_user.id, calories)
    
    user_data = await state.get_data()
    food_name = user_data.get('food_name', 'Продукт')
    
    await message.answer(f"✅ Записано: *{food_name}* — {calories} ккал.")
    await message.answer("📋 Главное меню:", reply_markup=keyboards.get_main_menu_keyboard())
    await state.clear()