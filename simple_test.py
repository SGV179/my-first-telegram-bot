import requests
from database.cloud_config import CLICKHOUSE_CONFIG

def test_connection():
    try:
        # Простой HTTP запрос к ClickHouse
        url = f"http://{CLICKHOUSE_CONFIG['host']}:{CLICKHOUSE_CONFIG['port']}/"
        response = requests.get(url, timeout=5)
        print(f"✅ HTTP статус: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка HTTP подключения: {e}")

if __name__ == "__main__":
    test_connection()
