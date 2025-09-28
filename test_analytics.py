#!/usr/bin/env python3
"""
Тест аналитики - проверка подключения к БД и работы с данными
"""

from services.analytics import AnalyticsService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 🔐 Данные подключения (те же, что в test_final.py)
DB_CONFIG = {
    "host": "rc1a-7juj18i6akmu5ec1.mdb.yandexcloud.net",
    "port": 6432,
    "user": "bot_admin",
    "password": "kL6-TUk-i7N-Djz",  # ⬅️ ВВЕДИТЕ ПАРОЛЬ ЗДЕСЬ
    "database": "tg_admin_bot",
    "sslmode": "require"
}

def get_db_session():
    """Создает сессию базы данных"""
    connection_string = (
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        "?sslmode=require"
    )
    
    engine = create_engine(connection_string, echo=True)
    Session = sessionmaker(bind=engine)
    return Session()

def test_analytics():
    print("🧪 Запуск теста аналитики...")
    print("Подключаемся к МАСТЕР-СЕРВЕРУ: rc1a-7juj18i6akmu5ec1.mdb.yandexcloud.net")
    
    # Создаем сессию базы данных
    db = get_db_session()
    print("✅ Сессия базы данных создана")
    
    # Инициализируем аналитику с передачей базы данных
    analytics = AnalyticsService(db)
    print("✅ Сервис аналитики инициализирован")
    
    # 1. Сначала создаем тестового пользователя
    print("\n1. Создаем тестового пользователя...")
    user = analytics.get_or_create_user(
        telegram_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    
    # 2. Теперь добавляем событие для этого пользователя
    print("\n2. Добавляем событие...")
    event = analytics.track_event(
        user_id=user.id,  # Используем реальный ID пользователя
        event_type="subscribe",
        channel_id=-1002581031645,
        event_data={"source": "bot"}
    )
    print(f"✅ Событие записано: {event.event_type} (ID: {event.id})")
    
    # 3. Тестируем получение статистики
    print("\n3. Получаем статистику...")
    stats = analytics.get_daily_stats(-1002581031645)
    print(f"📊 Статистика: {stats}")
    
    # 4. Проверим создание нескольких событий
    print("\n4. Добавляем еще события...")
    event2 = analytics.track_event(
        user_id=user.id,
        event_type="view",
        channel_id=-1002581031645,
        post_id=123,
        event_data={"duration": 30}
    )
    print(f"✅ Событие записано: {event2.event_type} (ID: {event2.id})")
    
    # 5. Проверим получение пользователя
    print("\n5. Проверяем получение пользователя...")
    same_user = analytics.get_or_create_user(telegram_id=123456789)
    print(f"✅ Пользователь получен: {same_user.username} (ID: {same_user.id})")
    
    # Закрываем соединение
    db.close()
    print("\n🎉 Все тесты пройдены успешно!")

if __name__ == "__main__":
    test_analytics()
