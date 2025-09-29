import requests
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

def get_bot_info():
    """Получает информацию о боте"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    
    try:
        response = requests.get(url)
        result = response.json()
        
        if result.get('ok'):
            bot_info = result['result']
            print(f"🤖 Бот: {bot_info['first_name']} (@{bot_info['username']})")
            print(f"🆔 ID бота: {bot_info['id']}")
            return True
        else:
            print(f"❌ Ошибка: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка получения информации: {e}")
        return False

def setup_webhook():
    """Настраивает бота для получения обновлений"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setChatMenuButton"
    
    data = {
        "menu_button": {
            "type": "default"
        }
    }
    
    try:
        response = requests.post(url, json=data)
        result = response.json()
        
        if result.get('ok'):
            print("✅ Настройки бота обновлены")
        else:
            print(f"⚠️  Предупреждение: {result}")
            
    except Exception as e:
        print(f"❌ Ошибка настройки: {e}")

if __name__ == "__main__":
    print("=== Информация о боте ===")
    if get_bot_info():
        print("\n=== Настройка вебхуков ===")
        setup_webhook()
    else:
        print("\n❌ Не удалось получить информацию о боте. Проверьте BOT_TOKEN в .env файле.")
