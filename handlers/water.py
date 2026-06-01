from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
import database
import keyboards
from states import WaterStates

router = Router()

def check_water_limit(current_water: int, water_goal: int) -> str:
    if current_water > water_goal:
        return "\n\n⚠️ *Внимание:* Ты превысил дневную норму воды! Всё хорошего в меру. 🙌"
    return f"\n\nОсталось выпить: {max(0, water_goal - current_water)} мл."

@router.callback_query(F.data == "menu_water")
async def callback_menu_water(callback: types.CallbackQuery):
    user = database.get_user_profile(callback.from_user.id)
    if not user:
        await callback.message.edit_text("⚠️ Сначала заполни анкету через /start", reply_markup=keyboards.get_back_to_menu_keyboard())
        await callback.answer()
        return

    log = database.get_or_create_daily_log(callback.from_user.id)
    status = check_water_limit(log['water_ml'], user['water_goal'])
    
    text = f"💧 *Дневник воды:*\n\n• Выпито: {log['water_ml']} мл\n• Норма: {user['water_goal']} мл{status}"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboards.get_water_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("add_water_") & F.data.split("_")[2].cast(str).isdigit())
async def callback_add_water(callback: types.CallbackQuery):
    user = database.get_user_profile(callback.from_user.id)
    if not user:
        await callback.message.edit_text("⚠️ Сначала заполни анкету через /start", reply_markup=keyboards.get_back_to_menu_keyboard())
        await callback.answer()
        return

    amount = int(callback.data.split("_")[2])
    database.add_water_to_db(callback.from_user.id, amount)
    
    log = database.get_or_create_daily_log(callback.from_user.id)
    status = check_water_limit(log['water_ml'], user['water_goal'])
    
    text = f"💧 *Дневник воды:*\n\n• Выпито: {log['water_ml']} мл\n• Норма: {user['water_goal']} мл{status}"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboards.get_water_keyboard())
    await callback.answer(f"Добавлено {amount} мл! 🥤")

@router.callback_query(F.data == "add_water_custom")
async def callback_add_water_custom(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите количество выпитой воды (мл):")
    await state.set_state(WaterStates.waiting_for_custom_water)
    await callback.message.delete()
    await callback.answer()

@router.message(WaterStates.waiting_for_custom_water)
async def process_custom_water(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введи число!")
        return
    amount = int(message.text)
    database.add_water_to_db(message.from_user.id, amount)
    await message.answer(f"✅ Записано: {amount} мл воды.")
    await message.answer("📋 Главное меню:", reply_markup=keyboards.get_main_menu_keyboard())
    await state.clear()