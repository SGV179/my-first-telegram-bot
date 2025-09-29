from aiogram import Bot, types
from aiogram.filters import ChatMemberUpdatedFilter
from database.connections import get_db
from database.models import User, ChannelSubscription, UserEvent, UserScore
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

async def handle_chat_member_update(update: types.ChatMemberUpdated, bot: Bot):
    """Обрабатывает подписки и отписки пользователей в каналах"""
    try:
        logger.info(f"🔔 Получено обновление участника: {update.model_dump_json()}")
        
        user = update.new_chat_member.user
        chat = update.chat
        
        logger.info(f"👤 Пользователь: {user.id} (@{user.username})")
        logger.info(f"📢 Чат: {chat.id} ({chat.title})")
        logger.info(f"🔄 Статус: {update.old_chat_member.status} -> {update.new_chat_member.status}")
        
        # Проверяем, что это наши целевые каналы
        target_channels = list(settings.CHANNELS.values())
        if chat.id not in target_channels:
            logger.info(f"❌ Пропускаем канал {chat.id} - не в списке отслеживания")
            return
        
        logger.info(f"✅ Канал {chat.id} в списке отслеживания")
        
        # Определяем тип события
        if update.new_chat_member.status == "member":
            event_type = "subscribe"
            is_subscribed = True
            score_change = settings.SCORING["welcome"]
            logger.info(f"🎯 Событие: ПОДПИСКА")
        elif update.new_chat_member.status in ["left", "kicked"]:
            event_type = "unsubscribe" 
            is_subscribed = False
            score_change = 0
            logger.info(f"🎯 Событие: ОТПИСКА")
        else:
            logger.info(f"❌ Неизвестный статус: {update.new_chat_member.status}")
            return
        
        db = next(get_db())
        
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
            logger.info(f"✅ Создан новый пользователь: {user.id}")
        else:
            logger.info(f"✅ Найден существующий пользователь: {db_user.id}")
        
        # Обновляем подписку
        subscription = db.query(ChannelSubscription).filter(
            ChannelSubscription.user_id == db_user.id,
            ChannelSubscription.channel_id == chat.id
        ).first()
        
        if subscription:
            subscription.is_subscribed = is_subscribed
            logger.info(f"✅ Обновлена подписка пользователя {user.id}")
        else:
            subscription = ChannelSubscription(
                user_id=db_user.id,
                channel_id=chat.id,
                is_subscribed=is_subscribed
            )
            db.add(subscription)
            logger.info(f"✅ Создана новая подписка для пользователя {user.id}")
        
        # Записываем событие
        event = UserEvent(
            user_id=db_user.id,
            event_type=event_type,
            channel_id=chat.id,
            event_data={
                "chat_title": chat.title,
                "old_status": update.old_chat_member.status,
                "new_status": update.new_chat_member.status
            }
        )
        db.add(event)
        logger.info(f"✅ Записано событие: {event_type}")
        
        # Обновляем баллы для подписок
        if event_type == "subscribe":
            user_score = db.query(UserScore).filter(UserScore.user_id == db_user.id).first()
            if not user_score:
                user_score = UserScore(user_id=db_user.id, total_score=score_change)
                db.add(user_score)
                logger.info(f"⭐ Начислены приветственные баллы: {score_change}")
            else:
                user_score.total_score += score_change
                logger.info(f"⭐ Обновлены баллы пользователя: {user_score.total_score}")
        
        db.commit()
        logger.info(f"🎉 Успешно обработано: {user.id} {event_type} в {chat.title}")
        
    except Exception as e:
        logger.error(f"💥 Ошибка обработки подписки: {e}")
        import traceback
        logger.error(traceback.format_exc())
