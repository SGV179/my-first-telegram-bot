import logging
from aiogram import Bot
from app.config.config import config
from app.services.user_service import UserService
from app.services.points_service import PointsService

logger = logging.getLogger(__name__)

class ChannelService:
    @staticmethod
    async def check_user_subscription(bot: Bot, user_id: int):
        """Check if user is subscribed to both channels"""
        try:
            # Check subscription to channel 1
            member1 = await bot.get_chat_member(config.CHANNEL_1_ID, user_id)
            subscribed_1 = member1.status in ['member', 'administrator', 'creator']
            
            # Check subscription to channel 2
            member2 = await bot.get_chat_member(config.CHANNEL_2_ID, user_id)
            subscribed_2 = member2.status in ['member', 'administrator', 'creator']
            
            # Update user subscription status
            UserService.update_subscription_status(
                telegram_id=user_id,
                channel_1=subscribed_1,
                channel_2=subscribed_2
            )
            
            # Give welcome points if eligible
            if subscribed_1 and subscribed_2:
                welcome_points = UserService.give_welcome_points(user_id)
                if welcome_points > 0:
                    return {
                        'subscribed': True,
                        'channel_1': subscribed_1,
                        'channel_2': subscribed_2,
                        'welcome_points': welcome_points
                    }
            
            return {
                'subscribed': subscribed_1 and subscribed_2,
                'channel_1': subscribed_1,
                'channel_2': subscribed_2,
                'welcome_points': 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking subscription for user {user_id}: {e}")
            return {
                'subscribed': False,
                'channel_1': False,
                'channel_2': False,
                'welcome_points': 0
            }

    @staticmethod
    async def require_subscription(bot: Bot, user_id: int, message_text: str = None):
        """Check subscription and return appropriate message"""
        subscription = await ChannelService.check_user_subscription(bot, user_id)
        
        if not subscription['subscribed']:
            if message_text:
                return f"""
{message_text}

📋 Для продолжения необходимо подписаться на оба канала:

{config.CHANNEL_1}
{config.CHANNEL_2}

✅ После подписки используйте команду /start для проверки
                """
            else:
                return f"""
❌ Для доступа к этому функционалу необходимо подписаться на оба канала:

{config.CHANNEL_1}
{config.CHANNEL_2}

✅ После подписки используйте команду /start для проверки
                """
        
        # If subscribed and got welcome points
        if subscription['welcome_points'] > 0:
            return f"""
✅ Вы подписаны на оба канала!

🎉 Вам начислено {subscription['welcome_points']} приветственных баллов!

💰 Теперь вы можете участвовать в программе лояльности и зарабатывать баллы за активность.
            """
        
        # If already subscribed
        return "✅ Вы подписаны на оба канала! Можете продолжать использование бота."
