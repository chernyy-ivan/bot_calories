from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
import database
import keyboards
from states import WeightStates

router = Router()

@router.callback_query(F.data == "track_weight")
async def callback_track_weight(callback: types.CallbackQuery, state: FSMContext):
    user = database.get_user_profile(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "⚠️ Сначала заполни анкету через /start", 
            reply_markup=keyboards.get_back_to_menu_keyboard()
        )
        await callback.answer()
        return

    await callback.message.answer(
        f"📋 Твой текущий вес в профиле: *{user['current_weight']} кг*.\n"
        "Введи свой новый вес на сегодня (в кг):", 
        parse_mode="Markdown"
    )
    await state.set_state(WeightStates.waiting_for_new_weight)
    await callback.message.delete()
    await callback.answer()

@router.message(WeightStates.waiting_for_new_weight)
async def process_new_weight(message: types.Message, state: FSMContext):
    try:
        new_weight = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введи вес числом (например: 84.5 или 72)!")
        return

    if new_weight <= 0 or new_weight > 300:
        await message.answer("Введи реальный вес!")
        return

    # Получаем данные пользователя до обновления
    user = database.get_user_profile(message.from_user.id)
    old_weight = user['current_weight']
    
    # Обновляем БД и пересчитываем нормы
    database.update_weight_and_recalculate(message.from_user.id, new_weight)

    # Логика мотивирующих уведомлений с проверкой безопасности
    if new_weight < old_weight:
        diff = round(old_weight - new_weight, 2)
        
        # Предупреждение о резкой потере веса (более 3 кг)
        if diff > 3.0:
            motivation = (
                f"⚠️ *Внимание! Слишком большая потеря веса ({diff} кг).* ⚠️\n\n"
                "Такой резкий скачок может быть опасен для организма. Возможно, произошла ошибка при взвешивании или вводе данных.\n\n"
                "_Если вы ошиблись с записанным весом, просто введите его заново._"
            )
        else:
            motivation = (
                f"📉 *Минус {diff} кг! Отличный результат!* 🎉\n\n"
                "Ты просто красавчик, твои усилия дают реальные плоды! Процесс запущен, жиросжигание идет полным ходом. "
                "Главное — продолжай в том же духе, держи планку и не сбавляй обороты.\n\n"
                "_Если вы ошиблись с записанным весом, просто введите его заново._"
            )
            
    elif new_weight > old_weight:
        diff = round(new_weight - old_weight, 2)
        motivation = (
            f"📈 *Плюс {diff} кг. Без паники!* ⚖️\n\n"
            "Слушай, это абсолютно естественный процесс. Вес постоянно колеблется из-за задержки воды. "
            "Это НЕ новый жир! Ни в коем случае *не думай бросать*.\n\n"
            "_Если вы ошиблись с записанным весом, просто введите его заново._"
        )
    else:
        motivation = (
            "⚖️ *Вес закрепился! Уверенная стабильность.* 🎯\n\n"
            "Организм адаптируется к новым условиям и фиксирует результат — это очень хороший знак. "
            "Работаем дальше!\n\n"
            "_Если вы ошиблись с записанным весом, просто введите его заново._"
        )

    await message.answer(motivation, parse_mode="Markdown")
    await message.answer("📋 Главное меню:", reply_markup=keyboards.get_main_menu_keyboard())
    await state.clear()