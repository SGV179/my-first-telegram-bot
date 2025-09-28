#!/usr/bin/env python3
"""
Финальный тест подключения с правильными данными
"""

import psycopg2

# 🔐 ЗАМЕНИТЕ ЭТИ ДАННЫЕ НА РЕАЛЬНЫЕ ИЗ YANDEX CLOUD CONSOLE
DB_CONFIG = {
    "host": "rc1a-7juj18i6akmu5ec1.mdb.yandexcloud.net",
    "port": 6432,
    "user": "bot_admin",  # ⬅️ ИЗ ВКЛАДКИ "ПОЛЬЗОВАТЕЛИ"
    "password": "kL6-TUk-i7N-Djz",  # ⬅️ ПАРОЛЬ ПОЛЬЗОВАТЕЛЯ
    "database": "tg_admin_bot",  # ⬅️ ИЗ ВКЛАДКИ "БАЗЫ ДАННЫХ"
    "sslmode": "require"
}

def test_connection():
    print("🧪 Финальный тест подключения...")
    print(f"🔗 Хост: {DB_CONFIG['host']}")
    print(f"👤 Пользователь: {DB_CONFIG['user']}")
    print(f"📁 База: {DB_CONFIG['database']}")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Проверяем версию PostgreSQL
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Подключение успешно!")
        print(f"📋 Версия: {version[0]}")
        
        # Проверяем таблицы
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Таблицы в базе ({len(tables)}):")
        for table in tables:
            print(f"  - {table}")
        
        cursor.close()
        conn.close()
        print("🎉 Все работает отлично!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\n🔧 Проверьте:")
        print("1. Правильность username, password, database name")
        print("2. Что пользователь имеет доступ к базе")
        print("3. Что ваш IP добавлен в security groups")

if __name__ == "__main__":
    test_connection()
