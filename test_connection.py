import sys
import os

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connections import create_tables, engine
from sqlalchemy import text  # Добавляем этот импорт

def test_connection():
    try:
        # Пытаемся создать таблицы (проверит подключение)
        create_tables()
        print("✅ Подключение к PostgreSQL успешно!")
        print("✅ Таблицы созданы/проверены")
        
        # Проверяем существующие таблицы (исправленный синтаксис)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            print(f"✅ Найдены таблицы: {tables}")
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
