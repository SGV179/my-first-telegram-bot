import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database.connections import create_tables, get_db
from database.models import User, ChannelSubscription, UserEvent, UserScore

load_dotenv()

async def test_channel_tracking():
    """Тестирует систему отслеживания подписчиков"""
    
    # Создаем таблицы
    create_tables()
    print("✅ База данных инициализирована")
    
    # Проверяем текущие данные
    db = next(get_db())
    
    users = db.query(User).all()
    subscriptions = db.query(ChannelSubscription).all()
    events = db.query(UserEvent).all()
    scores = db.query(UserScore).all()
    
    print(f"\n📊 Текущая статистика базы данных:")
    print(f"   👤 Пользователей: {len(users)}")
    print(f"   📝 Подписок: {len(subscriptions)}")
    print(f"   🎯 Событий: {len(events)}")
    print(f"   ⭐ Записей баллов: {len(scores)}")
    
    if users:
        print(f"\n📋 Список пользователей в базе:")
        for user in users:
            user_subs = db.query(ChannelSubscription).filter(ChannelSubscription.user_id == user.id).all()
            user_score = db.query(UserScore).filter(UserScore.user_id == user.id).first()
            score = user_score.total_score if user_score else 0
            
            print(f"   👤 {user.first_name or 'No name'} (@{user.username or 'no_username'})")
            print(f"      ID: {user.telegram_id}, Баллы: {score}")
            print(f"      Подписки: {len(user_subs)}")
            
            for sub in user_subs:
                status = "✅ подписан" if sub.is_subscribed else "❌ отписан"
                print(f"        - Канал {sub.channel_id}: {status}")

def check_bot_channel_status():
    """Проверяет статус бота в каналах"""
    print(f"\n🔍 Проверка статуса бота в каналах:")
    
    # ID каналов из настроек
    channels = {
        "golden_square": -1002581031645,
        "golden_asset": -1002582539663
    }
    
    print("   Каналы для отслеживания:")
    for name, channel_id in channels.items():
        print(f"   • {name}: {channel_id}")
    
    print(f"\n💡 Для тестирования:")
    print(f"   1. Пригласите пользователя в канал @golden_square_1")
    print(f"   2. Исключите пользователя из канала")
    print(f"   3. Запустите этот тест снова чтобы увидеть изменения")

if __name__ == "__main__":
    print("=== Тест системы отслеживания каналов ===\n")
    asyncio.run(test_channel_tracking())
    check_bot_channel_status()
