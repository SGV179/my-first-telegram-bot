import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from app.services.activity_service import ActivityService
from app.services.points_service import PointsService
from app.services.admin_service import AdminService

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("activities"))
async def activities_handler(message: Message):
    """Show user activity history"""
    try:
        user_id = message.from_user.id
        activities = ActivityService.get_user_activities(user_id, limit=10)
        
        if not activities:
            await message.answer("📊 У вас пока нет зарегистрированных активностей.")
            return
        
        activities_text = "📊 История ваших активностей:\n\n"
        
        for i, activity in enumerate(activities, 1):
            activity_type, points_earned, channel_id, created_at = activity
            
            # Translate activity types to Russian
            activity_names = {
                'like': '❤️ Лайк',
                'comment': '💬 Комментарий', 
                'repost': '🔄 Репост',
                'button_click': '🔘 Нажатие кнопки',
                'welcome_bonus': '🎉 Приветственные баллы',
                'admin_bonus': '🛠️ Начисление админа'
            }
            
            activity_name = activity_names.get(activity_type, activity_type)
            
            activities_text += f"{i}. {activity_name}\n"
            activities_text += f"   💰 +{points_earned} баллов\n"
            activities_text += f"   📅 {created_at.strftime('%d.%m.%Y %H:%M')}\n"
            activities_text += "   ─────────────────\n"
        
        total_points = PointsService.get_user_points(user_id)
        activities_text += f"\n💰 Ваш текущий баланс: {total_points} баллов"
        
        await message.answer(activities_text)
        
    except Exception as e:
        logger.error(f"❌ Error in activities handler: {e}")
        await message.answer("❌ Произошла ошибка при получении истории активностей")

@router.message(Command("activity_stats"))
async def activity_stats_handler(message: Message):
    """Show activity statistics (admin only)"""
    try:
        if not AdminService.is_admin(message.from_user.id):
            await message.answer("❌ У вас нет прав администратора.")
            return
            
        stats = ActivityService.get_activities_stats(days=7)
        top_users = ActivityService.get_top_active_users(limit=5, days=7)
        
        if not stats:
            await message.answer("📊 Нет данных об активностях за последние 7 дней.")
            return
        
        stats_text = "📊 Статистика активностей (7 дней):\n\n"
        
        total_activities = 0
        total_points = 0
        
        for stat in stats:
            activity_type, count, points = stat
            
            activity_names = {
                'like': '❤️ Лайки',
                'comment': '💬 Комментарии',
                'repost': '🔄 Репосты', 
                'button_click': '🔘 Нажатия кнопок',
                'welcome_bonus': '🎉 Приветственные',
                'admin_bonus': '🛠️ Админ начисления'
            }
            
            activity_name = activity_names.get(activity_type, activity_type)
            stats_text += f"{activity_name}: {count} (+{points} баллов)\n"
            
            total_activities += count
            total_points += points
        
        stats_text += f"\n📈 Всего активностей: {total_activities}"
        stats_text += f"\n💰 Всего баллов: {total_points}"
        
        if top_users:
            stats_text += "\n\n🏆 Самые активные пользователи:\n"
            for i, user in enumerate(top_users, 1):
                user_id, username, first_name, activity_count, user_points = user
                stats_text += f"{i}. {first_name} (@{username or 'нет'}): {activity_count} активностей (+{user_points} баллов)\n"
        
        await message.answer(stats_text)
        
    except Exception as e:
        logger.error(f"❌ Error in activity_stats handler: {e}")
        await message.answer("❌ Произошла ошибка при получении статистики активностей")

@router.message(Command("test_activity"))
async def test_activity_handler(message: Message):
    """Test activity tracking (for demonstration)"""
    try:
        user_id = message.from_user.id
        
        # Test different activity types
        test_activities = [
            ('like', 'Тестовый лайк'),
            ('comment', 'Тестовый комментарий'),
            ('repost', 'Тестовый репост'),
            ('button_click', 'Тестовое нажатие кнопки')
        ]
        
        results = []
        for activity_type, description in test_activities:
            success = ActivityService.track_activity(
                user_id, 
                activity_type, 
                description=description
            )
            if success:
                results.append(f"✅ {description}")
            else:
                results.append(f"❌ {description}")
        
        response_text = "🧪 Тест отслеживания активностей:\n\n" + "\n".join(results)
        response_text += f"\n\n📊 Ваши активности: /activities"
        
        await message.answer(response_text)
        
    except Exception as e:
        logger.error(f"❌ Error in test_activity handler: {e}")
        await message.answer("❌ Произошла ошибка при тестировании активностей")
