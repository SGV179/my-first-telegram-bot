import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Токен бота
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # ID каналов для администрирования
    CHANNELS = {
        "golden_square": -1002581031645,
        "golden_asset": -1002582539663
    }
    
    # Настройки баллов
    SCORING = {
        "welcome": 30,           # Приветственные баллы
        "comment": 5,            # За комментарий
        "repost": 3,             # За репост
        "like": 1,               # За лайк
        "dislike": -1,           # За дизлайк
        "referral": 50           # За приглашенного пользователя
    }
    
    # Роли пользователей
    ROLES = {
        "admin": "admin",
        "user": "user", 
        "client": "client"
    }

settings = Settings()
