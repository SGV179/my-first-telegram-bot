from database.connections import create_tables, get_db
from database.models import User, ChannelSubscription, UserEvent, UserScore
from config.settings import settings
from datetime import datetime
import json

def test_detailed_tracking():
    """Детальная проверка сохраненных данных"""
    
    create_tables()
    print("✅ База данных инициализирована\n")
    
    db = next(get_db())
    
    # Проверяем пользователей
    users = db.query(User).all()
    print(f"📊 Пользователей в базе: {len(users)}")
    
    for user in users:
        print(f"\n👤 Пользователь #{user.id}:")
        print(f"   Telegram ID: {user.telegram_id}")
        print(f"   Имя: {user.first_name}")
        print(f"   Username: @{user.username}")
        print(f"   Дата регистрации: {user.registration_date}")
        
        # Подписки пользователя
        subscriptions = db.query(ChannelSubscription).filter(
            ChannelSubscription.user_id == user.id
        ).all()
        
        print(f"   📝 Подписок: {len(subscriptions)}")
        for sub in subscriptions:
            channel_name = "Неизвестный канал"
            for name, channel_id in settings.CHANNELS.items():
                if channel_id == sub.channel_id:
                    channel_name = name
                    break
            
            status = "✅ подписан" if sub.is_subscribed else "❌ отписан"
            print(f"      • {channel_name} ({sub.channel_id}): {status}")
            print(f"        Дата подписки: {sub.subscribed_at}")
        
        # Баллы пользователя
        user_score = db.query(UserScore).filter(UserScore.user_id == user.id).first()
        score = user_score.total_score if user_score else 0
        print(f"   ⭐ Баллы: {score}")
        
        # События пользователя
        events = db.query(UserEvent).filter(UserEvent.user_id == user.id).all()
        print(f"   🎯 Событий: {len(events)}")
        
        for event in events[-3:]:  # Последние 3 события
            channel_name = "Неизвестный канал"
            for name, channel_id in settings.CHANNELS.items():
                if channel_id == event.channel_id:
                    channel_name = name
                    break
            
            print(f"      • {event.event_type} в {channel_name}")
            print(f"        Время: {event.created_at}")
            if event.event_data:
                print(f"        Данные: {json.dumps(event.event_data, ensure_ascii=False)}")

def check_recent_activity():
    """Проверяет последнюю активность"""
    db = next(get_db())
    
    print(f"\n📈 Последняя активность:")
    
    # Последние события
    recent_events = db.query(UserEvent).order_by(UserEvent.created_at.desc()).limit(5).all()
    
    if recent_events:
        print("Последние 5 событий:")
        for event in recent_events:
            user = db.query(User).filter(User.id == event.user_id).first()
            user_name = f"{user.first_name} (@{user.username})" if user else f"ID: {event.user_id}"
            
            channel_name = "Неизвестный канал"
            for name, channel_id in settings.CHANNELS.items():
                if channel_id == event.channel_id:
                    channel_name = name
                    break
            
            print(f"  • {user_name}: {event.event_type} в {channel_name}")
            print(f"    Время: {event.created_at}")
    else:
        print("  Нет событий за последнее время")

if __name__ == "__main__":
    print("=== Детальная проверка системы отслеживания ===\n")
    test_detailed_tracking()
    check_recent_activity()
