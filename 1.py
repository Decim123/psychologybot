import sqlite3

# Создаем соединение с базой данных (если файла базы данных нет, он будет создан)
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

# Создаем таблицу пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id TEXT NOT NULL,
    username TEXT,
    answer TEXT
)
''')

# Создаем таблицу администраторов
cursor.execute('''
CREATE TABLE IF NOT EXISTS administrators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id TEXT NOT NULL
)
''')

# Создаем таблицу с текстами ответов
cursor.execute('''
CREATE TABLE IF NOT EXISTS answers (
    start TEXT DEFAULT 'HELLO',
    q1 TEXT,
    q2 TEXT
)
''')

# Сохраняем изменения и закрываем соединение
conn.commit()
conn.close()

print("База данных и таблицы успешно созданы.")
