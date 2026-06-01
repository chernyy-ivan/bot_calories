import sqlite3
from datetime import date

DB_NAME = "tracker.db"

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
    
    conn.commit()
    conn.close()

def update_user_profile(user_id: int, username: str, age: int, height: int, 
                        current_weight: float, target_weight: float, target_months: int, 
                        calorie_goal: int, water_goal: int):
    """Сохраняет или обновляет данные профиля пользователя (Upsert)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO users (user_id, username, age, height, current_weight, target_weight, target_months, calorie_goal, water_goal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            age=excluded.age,
            height=excluded.height,
            current_weight=excluded.current_weight,
            target_weight=excluded.target_weight,
            target_months=excluded.target_months,
            calorie_goal=excluded.calorie_goal,
            water_goal=excluded.water_goal
    ''', (user_id, username, age, height, current_weight, target_weight, target_months, calorie_goal, water_goal))
    
    conn.commit()
    conn.close()

def get_user_profile(user_id: int):
    """Возвращает данные профиля пользователя по его id"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT age, height, current_weight, target_weight, target_months, calorie_goal, water_goal 
        FROM users WHERE user_id = ?
    ''', (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "age": row[0],
            "height": row[1],
            "current_weight": row[2],
            "target_weight": row[3],
            "target_months": row[4],
            "calorie_goal": row[5],
            "water_goal": row[6]
        }
    return None

def get_or_create_daily_log(user_id: int):
    """Находит или создает запись на сегодняшний день для конкретного пользователя"""
    current_date = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Пытаемся вставить пустую запись на сегодня, если её нет
    cursor.execute('''
        INSERT OR IGNORE INTO daily_logs (user_id, date, calories_consumed, calories_burned, water_ml, steps)
        VALUES (?, ?, 0, 0, 0, 0)
    ''', (user_id, current_date))
    
    conn.commit()
    
    # Забираем актуальные данные за сегодня
    cursor.execute('''
        SELECT calories_consumed, calories_burned, water_ml, steps 
        FROM daily_logs WHERE user_id = ? AND date = ?
    ''', (user_id, current_date))
    
    row = cursor.fetchone()
    conn.close()
    
    return {
        "calories_consumed": row[0],
        "calories_burned": row[1],
        "water_ml": row[2],
        "steps": row[3]
    }

def add_water_to_db(user_id: int, amount_ml: int):
    """Добавляет воду к сегодняшнему дню"""
    current_date = date.today().strftime("%Y-%m-%d")
    get_or_create_daily_log(user_id)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE daily_logs 
        SET water_ml = water_ml + ? 
        WHERE user_id = ? AND date = ?
    ''', (amount_ml, user_id, current_date))
    conn.commit()
    conn.close()

def add_calories_to_db(user_id: int, calories: int):
    """Добавляет потребленные калории к сегодняшнему дню"""
    current_date = date.today().strftime("%Y-%m-%d")
    get_or_create_daily_log(user_id)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE daily_logs 
        SET calories_consumed = calories_consumed + ? 
        WHERE user_id = ? AND date = ?
    ''', (calories, user_id, current_date))
    conn.commit()
    conn.close()