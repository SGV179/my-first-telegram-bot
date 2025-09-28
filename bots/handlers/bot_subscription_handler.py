from aiogram import Bot, types
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from database.connections import get_db
from database.models import User
from services.subscription_service import SubscriptionService
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

async def handle_bot_subscription(update: types.ChatMemberUpdated, bot: Bot):
    """Обрабатывает подписку и отписку от самого бота"""
    try:
        # Проверяем, что это обновление касается самого бота
        if update.new_chat_member.user.id != bot.id:
            return
        
        user = update.old_chat_member.user
        subscription_service = SubscriptionService(bot)
        
        if update.new_chat_member.status == "member":
            # Пользователь подписался на бота
            logger.info(f"Пользователь {user.id} подписался на бота")
            
            # Сохраняем пользователя в базу
            db = next(get_db())
            db_user = db.query(User).filter(User.telegram_id == user.id).first()
            if not db_user:
                db_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=settings.ROLES["user"]
                )
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
                logger.info(f"Создан новый пользователь бота: {user.id}")
            
            # Проверяем подписки на каналы и начисляем приветственные баллы
            if subscription_service.check_user_subscriptions(user.id):
                await subscription_service.update_user_score(user.id, settings.SCORING["welcome"], "welcome_bonus")
                await bot.send_message(
                    user.id,
                    f"🎉 Добро пожаловать! Вы получили {settings.SCORING['welcome']} приветственных баллов!\n\n"
                    f"Теперь вы участвуете в программе лояльности! 🎁"
                )
            else:
                await bot.send_message(
                    user.id,
                    "👋 Добро пожаловать! Подпишитесь на наши каналы чтобы получать баллы:\n"
                    f"• @golden_square_1\n"
                    f"• @golden_asset_1\n\n"
                    f"После подписки вы получите {settings.SCORING['welcome']} приветственных баллов! 🎁"
                )
                
        elif update.new_chat_member.status in ["left", "kicked"]:
            # Пользователь отписался от бота
            logger.info(f"Пользователь {user.id} отписался от бота")
            subscription_service.reset_user_score(user.id)
            
    except Exception as e:
        logger.error(f"Ошибка обработки подписки на бота: {e}")
