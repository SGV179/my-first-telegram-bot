from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
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

# Базовый класс для моделей
Base = declarative_base()

def create_tables():
    """Создает все таблицы в базе данных"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Генератор сессий для зависимостей"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
