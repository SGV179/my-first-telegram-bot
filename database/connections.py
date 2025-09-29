from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.base import Base  # Изменено импорт Base
from database.cloud_config import POSTGRES_CONFIG
import ssl

# SSL контекст
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Строка подключения к МАСТЕР-СЕРВЕРУ PostgreSQL
connection_string = f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"

print(f"Подключаемся к МАСТЕР-СЕРВЕРУ: {POSTGRES_CONFIG['host']}")

# Движок с SSL и настройками для записи
engine = create_engine(
    connection_string,
    connect_args={
        'sslmode': 'require',
        'sslrootcert': ssl_context,
        'options': '-c default_transaction_read_only=off'  # Явно выключаем read-only
    },
    echo=True,
    pool_pre_ping=True
)

# Создаем сессию для работы с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Создает все таблицы в базе данных"""
    # Импортируем все модели чтобы они зарегистрировались у Base
    from database import models
    from database import rewards_models
    
    Base.metadata.create_all(bind=engine)

def get_db():
    """Генератор сессий для зависимостей"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

