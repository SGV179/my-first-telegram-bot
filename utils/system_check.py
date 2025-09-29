from sqlalchemy import text
from database.connections import get_db

def check_system_health():
    """Проверяет здоровье системы"""
    print(f"🔧 ПРОВЕРКА СИСТЕМЫ:")
    
    try:
        db = next(get_db())
        
        # Проверяем подключение к БД
        db.execute(text("SELECT 1"))
        print("   ✅ База данных: подключение активно")
        
        # Проверяем основные таблицы
        tables = ['users', 'channel_subscriptions', 'user_events', 'user_scores']
        for table in tables:
            result = db.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"))
            exists = result.scalar()
            if exists:
                print(f"   ✅ Таблица {table}: существует")
            else:
                print(f"   ❌ Таблица {table}: отсутствует")
        
        print("   🎉 Система готова к работе!")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка проверки системы: {e}")
        return False

if __name__ == "__main__":
    check_system_health()
