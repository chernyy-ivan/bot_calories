from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👤 Мой профиль", callback_data="view_profile"))
    builder.row(
        types.InlineKeyboardButton(text="💧 Дневник Воды", callback_data="menu_water"),
        types.InlineKeyboardButton(text="🍎 Дневник Еды", callback_data="menu_food")
    )
    # Кнопка для записи веса
    builder.row(types.InlineKeyboardButton(text="⚖️ Записать новый вес", callback_data="track_weight"))
    builder.row(types.InlineKeyboardButton(text="⚙️ Перезаполнить анкету", callback_data="restart_survey"))
    return builder.as_markup()

def get_water_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="➕ 250 мл", callback_data="add_water_250"),
        types.InlineKeyboardButton(text="➕ 500 мл", callback_data="add_water_500")
    )
    builder.row(types.InlineKeyboardButton(text="✍️ Свой объём", callback_data="add_water_custom"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()

def get_food_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✍️ Записать еду", callback_data="add_food_prompt"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()

def get_back_to_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()