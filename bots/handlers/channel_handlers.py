from aiogram import Bot, Dispatcher, types
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from database.connections import get_db
from database.models import User, ChannelSubscription, UserEvent
from services.analytics import AnalyticsService
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class ChannelHandlers:
    def __init__(self, dp: Dispatcher, bot: Bot):
        self.dp = dp
        self.bot = bot
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрируем обработчики для каналов"""
        
        # Обработчик подписок/отписок на каналы
        self.dp.chat_member.register(
            self.handle_chat_member_update,
            ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER)  # Изменение статуса участника
        )
    
    async def handle_chat_member_update(self, update: types.ChatMemberUpdated):
        """Обрабатывает подписки и отписки пользователей в каналах"""
        try:
            db = next(get_db())
            analytics = AnalyticsService(db)
            
            user = update.new_chat_member.user
            chat = update.chat
            
            # Проверяем, что это наши целевые каналы
            if chat.id not in settings.CHANNELS.values():
                return
            
            # Определяем тип события
            if update.new_chat_member.status == "member":
                event_type = "subscribe"
                is_subscribed = True
                score_change = settings.SCORING["welcome"]
            elif update.new_chat_member.status in ["left", "kicked"]:
                event_type = "unsubscribe" 
                is_subscribed = False
                score_change = 0
            else:
                return
            
            # Сохраняем/обновляем пользователя
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
            
            # Обновляем подписку
            subscription = db.query(ChannelSubscription).filter(
                ChannelSubscription.user_id == db_user.id,
                ChannelSubscription.channel_id == chat.id
            ).first()
            
            if subscription:
                subscription.is_subscribed = is_subscribed
            else:
                subscription = ChannelSubscription(
                    user_id=db_user.id,
                    channel_id=chat.id,
                    is_subscribed=is_subscribed
                )
                db.add(subscription)
            
            # Записываем событие
            analytics.track_event(
                user_id=db_user.id,
                event_type=event_type,
                channel_id=chat.id,
                event_data={
                    "chat_title": chat.title,
                    "old_status": update.old_chat_member.status,
                    "new_status": update.new_chat_member.status
                }
            )
            
            # Обновляем баллы для подписок
            if event_type == "subscribe":
                user_score = db.query(UserScore).filter(UserScore.user_id == db_user.id).first()
                if not user_score:
                    user_score = UserScore(user_id=db_user.id, total_score=score_change)
                    db.add(user_score)
                else:
                    user_score.total_score += score_change
                    user_score.last_updated = update.date
            
            db.commit()
            
            logger.info(f"Пользователь {user.id} {event_type} в канале {chat.title}")
            
        except Exception as e:
            logger.error(f"Ошибка обработки подписки: {e}")
