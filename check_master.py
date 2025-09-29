import psycopg2
from database.cloud_config import POSTGRES_CONFIG

def check_master():
    try:
        conn = psycopg2.connect(
            host=POSTGRES_CONFIG['host'],
            port=POSTGRES_CONFIG['port'],
            database=POSTGRES_CONFIG['database'],
            user=POSTGRES_CONFIG['user'],
            password=POSTGRES_CONFIG['password'],
            sslmode='require'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT pg_is_in_recovery()")  # False = мастер, True = реплика
        is_replica = cursor.fetchone()[0]
        
        print(f"✅ Подключение к {POSTGRES_CONFIG['host']} успешно")
        print(f"📊 Это реплика: {is_replica} (False = МАСТЕР, True = РЕПЛИКА)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_master()
