from sqlalchemy import create_engine
from database.cloud_config import POSTGRES_CONFIG

# Подключаемся к базе данных postgres (системная БД)
admin_connection_string = f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/postgres?sslmode=require"

admin_engine = create_engine(admin_connection_string)

# Создаем новую базу данных
with admin_engine.connect() as conn:
    conn.execute("COMMIT")  # Завершаем любую транзакцию
    conn.execute(f"CREATE DATABASE {POSTGRES_CONFIG['database']}")
    print(f"✅ База данных {POSTGRES_CONFIG['database']} создана")

print("Теперь попробуйте снова test_analytics.py")
