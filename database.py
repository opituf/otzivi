import sqlite3
from config import ADMIN_PANEL_PASSWORD


def init_db():
    conn = sqlite3.connect('reviews.db')
    cursor = conn.cursor()

    # Создаем таблицу для отзывов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_rating INTEGER NOT NULL,
        staff_rating INTEGER NOT NULL,
        interior_rating INTEGER NOT NULL,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Создаем таблицу для администраторов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT NOT NULL
    )
    ''')

    # Добавляем стандартного администратора, если его нет
    cursor.execute('SELECT * FROM admins WHERE password = ?', (ADMIN_PANEL_PASSWORD,))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO admins (password) VALUES (?)', (ADMIN_PANEL_PASSWORD,))

    conn.commit()
    conn.close()


def add_review(food, staff, interior, comment=None):
    conn = sqlite3.connect('reviews.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO reviews (food_rating, staff_rating, interior_rating, comment)
    VALUES (?, ?, ?, ?)
    ''', (food, staff, interior, comment))
    conn.commit()
    conn.close()


def get_all_reviews():
    conn = sqlite3.connect('reviews.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reviews ORDER BY created_at DESC')
    reviews = cursor.fetchall()
    conn.close()
    return reviews


def format_review(review):
    return (
        f"Отзыв #{review[0]}\n"
        f"🍽 Еда: {review[1]}/5\n"
        f"👨‍🍳 Персонал: {review[2]}/5\n"
        f"🏠 Интерьер: {review[3]}/5\n"
        f"📝 Комментарий: {review[4] if review[4] else 'нет'}\n"
        f"📅 Дата: {review[5]}"
    )