from aiogram.fsm.state import State, StatesGroup

class ProfileStates(StatesGroup):
    waiting_for_age = State()
    waiting_for_height = State()
    waiting_for_weight = State()
    waiting_for_target_weight = State()
    waiting_for_months = State()

class WaterStates(StatesGroup):
    waiting_for_custom_water = State()

class FoodStates(StatesGroup):
    waiting_for_food_name = State()
    waiting_for_calories = State()

# Новое состояние для фиксации веса
class WeightStates(StatesGroup):
    waiting_for_new_weight = State()