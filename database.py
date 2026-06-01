import os
import sqlite3
from datetime import date

os.makedirs("data", exist_ok=True)
DB_NAME = os.path.join("data", "tracker.db")

def init_db():
    """Создает таблицы в базе данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            age INTEGER,
            height INTEGER,
            current_weight REAL,
            target_weight REAL,
            target_months INTEGER,
            calorie_goal INTEGER DEFAULT 2000,
            water_goal INTEGER DEFAULT 2000
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            calories_consumed INTEGER DEFAULT 0,
            calories_burned INTEGER DEFAULT 0,
            water_ml INTEGER DEFAULT 0,
            steps INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(user_id, date)
        )
    ''')

    # НОВАЯ ТАБЛИЦА: для хранения каждого съеденного блюда отдельно
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            food_name TEXT,
            calories INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def update_user_profile(user_id: int, username: str, age: int, height: int, 
                        current_weight: float, target_weight: float, target_months: int, 
                        calorie_goal: int, water_goal: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, username, age, height, current_weight, target_weight, target_months, calorie_goal, water_goal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username, age=excluded.age, height=excluded.height,
            current_weight=excluded.current_weight, target_weight=excluded.target_weight,
            target_months=excluded.target_months, calorie_goal=excluded.calorie_goal, water_goal=excluded.water_goal
    ''', (user_id, username, age, height, current_weight, target_weight, target_months, calorie_goal, water_goal))
    conn.commit()
    conn.close()


def add_steps_to_db(user_id: int, steps: int):
    current_date = date.today().strftime("%Y-%m-%d")
    get_or_create_daily_log(user_id)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE daily_logs SET steps = steps + ? WHERE user_id = ? AND date = ?', (steps, user_id, current_date))
    conn.commit()
    conn.close()


def get_user_profile(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT age, height, current_weight, target_weight, target_months, calorie_goal, water_goal FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"age": row[0], "height": row[1], "current_weight": row[2], "target_weight": row[3], "target_months": row[4], "calorie_goal": row[5], "water_goal": row[6]}
    return None

def get_or_create_daily_log(user_id: int):
    current_date = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO daily_logs (user_id, date, calories_consumed, calories_burned, water_ml, steps) VALUES (?, ?, 0, 0, 0, 0)', (user_id, current_date))
    conn.commit()
    cursor.execute('SELECT calories_consumed, calories_burned, water_ml, steps FROM daily_logs WHERE user_id = ? AND date = ?', (user_id, current_date))
    row = cursor.fetchone()
    conn.close()
    return {"calories_consumed": row[0], "calories_burned": row[1], "water_ml": row[2], "steps": row[3]}

def add_water_to_db(user_id: int, amount_ml: int):
    current_date = date.today().strftime("%Y-%m-%d")
    get_or_create_daily_log(user_id)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE daily_logs SET water_ml = water_ml + ? WHERE user_id = ? AND date = ?', (amount_ml, user_id, current_date))
    conn.commit()
    conn.close()

# ОБНОВЛЕННАЯ ФУНКЦИЯ: теперь сохраняет и общую сумму, и детальное блюдо
def add_calories_to_db(user_id: int, food_name: str, calories: int):
    """Добавляет блюдо в историю и обновляет суммарные калории за день"""
    current_date = date.today().strftime("%Y-%m-%d")
    get_or_create_daily_log(user_id)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Записываем отдельное блюдо в историю еды
    cursor.execute('''
        INSERT INTO food_logs (user_id, date, food_name, calories)
        VALUES (?, ?, ?, ?)
    ''', (user_id, current_date, food_name, calories))
    
    # 2. Обновляем общую сумму в дневном логе
    cursor.execute('''
        UPDATE daily_logs 
        SET calories_consumed = calories_consumed + ? 
        WHERE user_id = ? AND date = ?
    ''', (calories, user_id, current_date))
    
    conn.commit()
    conn.close()

# НОВАЯ ФУНКЦИЯ: достает список всего съеденного за сегодня
def get_daily_food_list(user_id: int):
    """Возвращает список всех съеденных блюд пользователя за сегодняшний день"""
    current_date = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT food_name, calories FROM food_logs 
        WHERE user_id = ? AND date = ?
        ORDER BY id ASC
    ''', (user_id, current_date))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Формируем список словарей [{food_name: "Борщ", calories: 250}, ...]
    return [{"food_name": row[0], "calories": row[1]} for row in rows]

def update_weight_and_recalculate(user_id: int, new_weight: float):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return None
    old_weight = user['current_weight']
    age = user['age']
    height = user['height']
    target_weight = user['target_weight']
    target_months = user['target_months']
    water_goal = int(new_weight * 30)
    bmr = (10 * new_weight) + (6.25 * height) - (5 * age) + 5
    weight_diff = new_weight - target_weight
    if weight_diff > 0:
        kg_per_month = weight_diff / target_months
        calorie_goal = int(bmr * 0.8) if kg_per_month > 4 else int(bmr * 0.9)
    elif weight_diff < 0:
        calorie_goal = int(bmr * 1.1)
    else:
        calorie_goal = int(bmr)
    cursor.execute('UPDATE users SET current_weight = ?, water_goal = ?, calorie_goal = ? WHERE user_id = ?', (new_weight, water_goal, calorie_goal, user_id))
    conn.commit()
    conn.close()
    return old_weight