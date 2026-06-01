from aiogram import Router
from . import common, water, food, weight, activity

# Создаем главный рутер обработчиков
router = Router()

# Вкладываем в него рутеры из отдельных файлов
router.include_routers(
    common.router,
    water.router,
    food.router,
    weight.router,
    activity.router,
)