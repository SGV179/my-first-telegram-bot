import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Токен бота
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # ID каналов для администрирования
    CHANNELS = {
        "golden_square": -1002581031645,  # @golden_square_1
        "golden_asset": -1002582539663    # @golden_asset_1
    }
    
    # Настройки баллов (программа лояльности)
    SCORING = {
        "welcome": 30,           # Приветственные баллы за подписку на бота и оба канала
        "comment": 5,            # За комментарий под постом или комментарием
        "repost": 3,             # За репост поста
        "like": 1,               # За лайк поста или комментария
        "dislike": 0,            # За дизлайк (не начисляется)
        "button_click": 10,      # За нажатие кнопки под постом
        "referral": 50           # За приглашенного пользователя
    }
    
    # Роли пользователей
    ROLES = {
        "admin": "admin",
        "user": "user", 
        "partner": "partner"  # Изменено с "client" на "partner"
    }
    
    # ID администраторов (добавьте сюда ваш Telegram ID)
    ADMINS = [8024125149, 197169077]  # Добавлены ID администраторов

settings = Settings()
