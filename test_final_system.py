from database.connections import create_tables, get_db
from database.models import User, ChannelSubscription, UserEvent, UserScore
from config.settings import settings
from datetime import datetime, timedelta
import json

def test_final_system():
    """Финальная проверка всей системы"""
    
    create_tables()
    print("🎯 ФИНАЛЬНАЯ ПРОВЕРКА СИСТЕМЫ\n")
    
    db = next(get_db())
    
    # Общая статистика
    total_users = db.query(User).count()
    total_subscriptions = db.query(ChannelSubscription).count()
    total_events = db.query(UserEvent).count()
    active_subscriptions = db.query(ChannelSubscription).filter(ChannelSubscription.is_subscribed == True).count()
    
    print("📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"   👤 Всего пользователей: {total_users}")
    print(f"   📝 Всего подписок: {total_subscriptions}")
    print(f"   ✅ Активных подписок: {active_subscriptions}")
    print(f"   🎯 Всего событий: {total_events}")
    
    # Статистика по каналам
    print(f"\n📺 СТАТИСТИКА ПО КАНАЛАМ:")
    for channel_name, channel_id in settings.CHANNELS.items():
        channel_subs = db.query(ChannelSubscription).filter(
            ChannelSubscription.channel_id == channel_id,
            ChannelSubscription.is_subscribed == True
        ).count()
        
        channel_events = db.query(UserEvent).filter(UserEvent.channel_id == channel_id).count()
        
        print(f"   • {channel_name} ({channel_id}):")
        print(f"     Подписчиков: {channel_subs}")
        print(f"     Событий: {channel_events}")
    
    # Последние события (за последние 24 часа)
    yesterday = datetime.now() - timedelta(days=1)
    recent_events = db.query(UserEvent).filter(UserEvent.created_at >= yesterday).count()
    
    print(f"\n⏰ АКТИВНОСТЬ ЗА ПОСЛЕДНИЕ 24 ЧАСА:")
    print(f"   Событий: {recent_events}")
    
    # Топ пользователей по баллам
    print(f"\n🏆 ТОП ПОЛЬЗОВАТЕЛЕЙ ПО БАЛЛАМ:")
    top_users = db.query(User, UserScore).join(UserScore, User.id == UserScore.user_id).order_by(UserScore.total_score.desc()).limit(5).all()
    
    if top_users:
        for i, (user, score) in enumerate(top_users, 1):
            print(f"   {i}. {user.first_name} (@{user.username}): {score.total_score} баллов")
    else:
        print("   Пока нет пользователей с баллами")
    
    # Проверяем систему начисления баллов
    print(f"\n💰 СИСТЕМА БАЛЛОВ:")
    print(f"   Приветственные баллы: {settings.SCORING['welcome']}")
    print(f"   За комментарий: {settings.SCORING['comment']}")
    print(f"   За репост: {settings.SCORING['repost']}")
    print(f"   За лайк: {settings.SCORING['like']}")

def check_system_health():
    """Проверяет здоровье системы"""
    print(f"\n🔧 ПРОВЕРКА СИСТЕМЫ:")
    
    try:
        db = next(get_db())
        
        # Проверяем подключение к БД
        db.execute("SELECT 1")
        print("   ✅ База данных: подключение активно")
        
        # Проверяем основные таблицы
        tables = ['users', 'channel_subscriptions', 'user_events', 'user_scores']
        for table in tables:
            result = db.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
            exists = result.scalar()
            if exists:
                print(f"   ✅ Таблица {table}: существует")
            else:
                print(f"   ❌ Таблица {table}: отсутствует")
        
        print("   🎉 Система готова к работе!")
        
    except Exception as e:
        print(f"   ❌ Ошибка проверки системы: {e}")

if __name__ == "__main__":
    print("=" * 50)
    test_final_system()
    check_system_health()
    print("=" * 50)
