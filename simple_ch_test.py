from clickhouse_driver import Client

def test_simple():
    try:
        # Подключаемся через HTTPS порт 8443
        client = Client(
            host='rc1a-f7cbaqtvudip1knj.mdb.yandexcloud.net',
            port=8443,  # HTTPS порт
            user='analytics_user',
            password='ваш_пароль',  # замените на реальный
            database='tg_analytics',
            secure=True,
            verify=False  # отключаем проверку SSL
        )
        
        result = client.execute('SELECT version()')
        print(f"✅ ClickHouse version: {result[0][0]}")
        
        # Покажем существующие таблицы
        tables = client.execute('SHOW TABLES')
        print(f"✅ Таблицы: {tables}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()
