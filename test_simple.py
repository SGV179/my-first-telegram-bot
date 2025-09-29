#!/usr/bin/env python3
"""
Простой тест подключения к БД
"""

from sqlalchemy import create_engine, text
import os

# Параметры подключения
DB_HOST = "rc1a-7juj18i6akmu5ec1.mdb.yandexcloud.net"
DB_USER = "ваш_username"  # Замените
DB_PASSWORD = "ваш_пароль"  # Замените
DB_NAME = "ваш_dbname"  # Замените
DB_PORT = "6432"

def test_connection():
    print("🧪 Тестируем простое подключение...")
    
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Подключение успешно! PostgreSQL version: {version}")
            
            # Проверим таблицы
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            print(f"📊 Таблицы в базе: {tables}")
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    test_connection()
