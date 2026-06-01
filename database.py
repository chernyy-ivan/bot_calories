import sqlite3

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