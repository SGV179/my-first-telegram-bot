from analytics.clickhouse_client import clickhouse_client
from analytics.events import analytics_manager

def test_clickhouse():
    try:
        # Простой тестовый запрос
        result = clickhouse_client.execute("SELECT version()")
        print(f"✅ ClickHouse version: {result[0][0]}")
        
        # Проверяем существующие таблицы
        tables = clickhouse_client.execute("SHOW TABLES")
        print(f"✅ Таблицы в ClickHouse: {[table[0] for table in tables]}")
        
        print("🎉 ClickHouse настроен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования ClickHouse: {e}")

if __name__ == "__main__":
    test_clickhouse()
