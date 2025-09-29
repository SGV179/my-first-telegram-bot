# Настройки для Yandex Cloud PostgreSQL
POSTGRES_CONFIG = {
    "host": "rc1a-7juj18i6akmu5ec1.mdb.yandexcloud.net",  # ЗАМЕНИТЕ на ваш хост
    "port": 6432,
    "database": "tg_admin_bot", 
    "user": "bot_admin",
    "password": "kL6-TUk-i7N-Djz"  # ЗАМЕНИТЕ на реальный пароль
}

# Настройки для Yandex Cloud ClickHouse
CLICKHOUSE_CONFIG = {
    "host": "rc1a-f7cbaqtvudip1knj.mdb.yandexcloud.net",
    "port": 8443,  # HTTPS порт (который открыт)
    "database": "tg_analytics", 
    "user": "analytics_user",
    "password": "179$kL6-TUk-i7N-Djz",
    "secure": True  # HTTPS
}
