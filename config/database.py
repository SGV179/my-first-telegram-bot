#!/usr/bin/env python3
"""
Конфигурация базы данных
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 🔐 Настройки подключения к БД
DB_CONFIG = {
    "host": "rc1a-7juj18i6akmu5ec1.mdb.yandexcloud.net",
    "port": 6432,
    "user": "bot_admin",
    "password": "kL6-TUk-i7N-Djz",  # ⬅️ ЗАМЕНИТЕ НА РЕАЛЬНЫЙ ПАРОЛЬ
    "database": "tg_admin_bot",
    "sslmode": "require"
}

def get_db_engine():
    """Создает и возвращает engine базы данных"""
    connection_string = (
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        "?sslmode=require"
    )
    
    engine = create_engine(connection_string, echo=False)  # echo=True для отладки
    return engine

def get_db_session():
    """Создает и возвращает сессию базы данных"""
    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_database():
    """Инициализирует базу данных (создает таблицы если нужно)"""
    from models import Base
    engine = get_db_engine()
    Base.metadata.create_all(engine)
    print("✅ База данных инициализирована")
