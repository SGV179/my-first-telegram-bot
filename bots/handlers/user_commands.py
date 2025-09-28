from aiogram import types
from aiogram.filters import Command
from database.connections import get_db
from database.models import User, ChannelSubscription, UserScore
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

async def cmd_stats(message: types.Message):
    """Показывает статистику пользователя"""
    try:
        db = next(get_db())
        user = message.from_user
        
        # Находим пользователя в базе
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        
        if not db_user:
            await message.answer(
                "📊 Вы еще не зарегистрированы в системе.\n"
                "Подпишитесь на один из наших каналов чтобы начать!"
            )
            return
        
        # Получаем подписки пользователя
        subscriptions = db.query(ChannelSubscription).filter(
            ChannelSubscription.user_id == db_user.id
        ).all()
        
        # Получаем баллы
        user_score = db.query(UserScore).filter(UserScore.user_id == db_user.id).first()
        total_score = user_score.total_score if user_score else 0
        
        # Формируем сообщение
        response = f"📊 Ваша статистика, {user.first_name}:\n\n"
        response += f"⭐ Всего баллов: {total_score}\n\n"
        response += "📺 Ваши подписки:\n"
        
        active_subs = 0
        for sub in subscriptions:
            channel_name = "Неизвестный канал"
            for name, channel_id in settings.CHANNELS.items():
                if channel_id == sub.channel_id:
                    channel_name = name
                    break
            
            status = "✅ подписан" if sub.is_subscribed else "❌ отписан"
            response += f"  • {channel_name}: {status}\n"
            if sub.is_subscribed:
                active_subs += 1
        
        response += f"\n🎯 Активных подписок: {active_subs} из {len(settings.CHANNELS)}"
        
        await message.answer(response)
        logger.info(f"Пользователь {user.id} запросил статистику")
        
    except Exception as e:
        logger.error(f"Ошибка в команде /stats: {e}")
        await message.answer("❌ Произошла ошибка при получении статистики")

async def cmd_channels(message: types.Message):
    """Показывает список каналов для подписки"""
    response = "📺 Наши каналы:\n\n"
    
    for name, channel_id in settings.CHANNELS.items():
        channel_username = {
            -1002581031645: "@golden_square_1",
            -1002582539663: "@golden_asset_1"
        }.get(channel_id, f"ID: {channel_id}")
        
        response += f"• {channel_username}\n"
    
    response += "\nПодпишитесь на каналы чтобы получать баллы! 🎁"
    
    await message.answer(response)
