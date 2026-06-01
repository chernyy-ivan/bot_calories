from aiogram import Router
from . import common, water, food, weight

# Создаем главный рутер обработчиков
router = Router()

# Вкладываем в него рутеры из отдельных файлов
router.include_routers(
    common.router,
    water.router,
    food.router,
    weight.router  # Наш новый рутер веса
)