#!/usr/bin/env python3
"""
Модуль для работы с базой данных
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os

def get_db_connection_string():
    """Возвращает строку подключения к базе данных"""
    return (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '6432')}/{os.getenv('DB_NAME')}"
    )

def init_db():
    """Инициализирует базу данных"""
    engine = create_engine(
        get_db_connection_string(),
        echo=True  # Логирование SQL запросов
    )
    
    # Создаем таблицы
    Base.metadata.create_all(engine)
    return engine

def get_db_session():
    """Возвращает сессию базы данных"""
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session()
