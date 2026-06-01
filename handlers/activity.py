from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database
import keyboards

router = Router()

class ActivityStates(StatesGroup):
    waiting_for_steps = State()

@router.callback_query(F.data == "add_steps_prompt")
async def callback_add_steps(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("🏃‍♂️ Сколько шагов ты сегодня прошел(ла)?")
    await state.set_state(ActivityStates.waiting_for_steps)
    await callback.answer()

@router.message(ActivityStates.waiting_for_steps)
async def process_steps(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введи число!")
        return
    database.add_steps_to_db(message.from_user.id, int(message.text))
    await message.answer(f"✅ Записано: {message.text} шагов.", reply_markup=keyboards.get_main_menu_keyboard())
    await state.clear()