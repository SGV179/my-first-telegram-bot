from database.connections import get_db
from database.models import User, UserScore
from database.rewards_models import Reward, RewardRedemption
from services.subscription_service import SubscriptionService
import logging

logger = logging.getLogger(__name__)

class RewardsService:
    def __init__(self):
        self.subscription_service = SubscriptionService()
    
    def get_available_rewards(self):
        """Возвращает список доступных наград"""
        try:
            db = next(get_db())
            rewards = db.query(Reward).filter(Reward.is_active == True).order_by(Reward.cost).all()
            return rewards
        except Exception as e:
            logger.error(f"Ошибка получения наград: {e}")
            return []
    
    def get_user_balance(self, user_id: int) -> int:
        """Возвращает баланс пользователя"""
        try:
            db = next(get_db())
            
            # Проверяем подписки
            if not self.subscription_service.check_user_subscriptions(user_id):
                return 0
            
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return 0
            
            user_score = db.query(UserScore).filter(UserScore.user_id == user.id).first()
            return user_score.total_score if user_score else 0
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return 0
    
    def redeem_reward(self, user_id: int, reward_id: int) -> dict:
        """Обмен баллов на награду"""
        try:
            db = next(get_db())
            
            # Проверяем подписки
            if not self.subscription_service.check_user_subscriptions(user_id):
                return {"success": False, "message": "❌ Для обмена баллов необходимо быть подписанным на бота и оба канала"}
            
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return {"success": False, "message": "❌ Пользователь не найден"}
            
            reward = db.query(Reward).filter(Reward.id == reward_id, Reward.is_active == True).first()
            if not reward:
                return {"success": False, "message": "❌ Награда не найдена"}
            
            user_score = db.query(UserScore).filter(UserScore.user_id == user.id).first()
            if not user_score or user_score.total_score < reward.cost:
                return {"success": False, "message": f"❌ Недостаточно баллов. Нужно: {reward.cost}, у вас: {user_score.total_score if user_score else 0}"}
            
            # Создаем запись об обмене
            redemption = RewardRedemption(
                user_id=user.id,
                reward_id=reward.id,
                status='pending'
            )
            db.add(redemption)
            
            # Списание баллов
            user_score.total_score -= reward.cost
            
            db.commit()
            
            logger.info(f"Пользователь {user_id} обменял {reward.cost} баллов на награду '{reward.name}'")
            
            return {
                "success": True, 
                "message": f"🎉 Поздравляем! Вы получили: {reward.name}\n\nОсталось баллов: {user_score.total_score}",
                "reward_name": reward.name,
                "remaining_balance": user_score.total_score
            }
            
        except Exception as e:
            logger.error(f"Ошибка обмена награды: {e}")
            return {"success": False, "message": "❌ Произошла ошибка при обмене баллов"}
    
    def get_user_redemptions(self, user_id: int):
        """Возвращает историю обменов пользователя"""
        try:
            db = next(get_db())
            
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return []
            
            redemptions = db.query(RewardRedemption).filter(
                RewardRedemption.user_id == user.id
            ).order_by(RewardRedemption.redeemed_at.desc()).limit(10).all()
            
            return redemptions
            
        except Exception as e:
            logger.error(f"Ошибка получения истории обменов: {e}")
            return []
