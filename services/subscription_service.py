from database.connections import get_db
from database.models import User, ChannelSubscription, UserScore
from config.settings import settings
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self, bot: Bot = None):
        self.bot = bot
    
    def check_user_subscriptions(self, user_id: int) -> bool:
        """Проверяет, подписан ли пользователь на бота и оба канала"""
        try:
            db = next(get_db())
            
            # Проверяем подписку на бота
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False
            
            # Проверяем подписки на каналы
            channel_subs = db.query(ChannelSubscription).filter(
                ChannelSubscription.user_id == user.id,
                ChannelSubscription.is_subscribed == True
            ).all()
            
            subscribed_channels = {sub.channel_id for sub in channel_subs}
            required_channels = set(settings.CHANNELS.values())
            
            # Пользователь должен быть подписан на все требуемые каналы
            return required_channels.issubset(subscribed_channels)
            
        except Exception as e:
            logger.error(f"Ошибка проверки подписок: {e}")
            return False
    
    async def update_user_score(self, user_id: int, score_change: int, action_type: str) -> bool:
        """Обновляет баллы пользователя с проверкой подписок"""
        try:
            db = next(get_db())
            
            # Проверяем подписки
            if not self.check_user_subscriptions(user_id):
                logger.info(f"Пользователь {user_id} не подписан на все каналы, баллы не начисляются")
                return False
            
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                logger.info(f"Пользователь {user_id} не найден в базе")
                return False
            
            user_score = db.query(UserScore).filter(UserScore.user_id == user.id).first()
            
            if not user_score:
                user_score = UserScore(user_id=user.id, total_score=0)
                db.add(user_score)
            
            user_score.total_score += score_change
            
            # Не допускаем отрицательные баллы
            if user_score.total_score < 0:
                user_score.total_score = 0
            
            db.commit()
            logger.info(f"Обновлены баллы пользователя {user_id}: {score_change} за {action_type}, всего: {user_score.total_score}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления баллов: {e}")
            return False
    
    def reset_user_score(self, user_id: int) -> bool:
        """Обнуляет баллы пользователя"""
        try:
            db = next(get_db())
            
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False
            
            user_score = db.query(UserScore).filter(UserScore.user_id == user.id).first()
            if user_score:
                user_score.total_score = 0
                db.commit()
                logger.info(f"Обнулены баллы пользователя {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обнуления баллов: {e}")
            return False
