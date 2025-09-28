import requests
import logging
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_chat_member_webhook():
    """Настраивает бота для получения обновлений участников чатов"""
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/setChatMenuButton"
    
    # Включаем получение обновлений участников
    data = {
        "menu_button": {
            "type": "default"
        }
    }
    
    try:
        response = requests.post(url, json=data)
        result = response.json()
        
        if result.get('ok'):
            logger.info("✅ Настройки меню бота обновлены")
        else:
            logger.error(f"❌ Ошибка: {result}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка настройки: {e}")

def get_bot_info():
    """Получает информацию о боте"""
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getMe"
    
    try:
        response = requests.get(url)
        result = response.json()
        
        if result.get('ok'):
            bot_info = result['result']
            print(f"🤖 Бот: {bot_info['first_name']} (@{bot_info['username']})")
            print(f"🆔 ID бота: {bot_info['id']}")
            print(f"✅ Бот активен: {bot_info['is_bot']}")
        else:
            print(f"❌ Ошибка: {result}")
            
    except Exception as e:
        print(f"❌ Ошибка получения информации: {e}")

if __name__ == "__main__":
    print("=== Информация о боте ===")
    get_bot_info()
    
    print("\n=== Настройка вебхуков ===")
    setup_chat_member_webhook()
