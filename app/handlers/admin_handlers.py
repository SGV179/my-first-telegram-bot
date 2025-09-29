import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.admin_service import AdminService
from app.services.user_service import UserService
from app.services.points_service import PointsService
from app.services.rewards_service import RewardsService

logger = logging.getLogger(__name__)

router = Router()

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_points_amount = State()
    waiting_for_points_reason = State()

# Простая проверка админа в каждом хендлере
async def check_admin(user_id: int) -> bool:
    return AdminService.is_admin(user_id)

@router.message(Command("admin"))
async def admin_panel_handler(message: Message):
    """Show admin panel"""
    if not await check_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
        
    try:
        # Get statistics
        user_stats = AdminService.get_user_stats()
        system_stats = AdminService.get_system_stats()
        
        admin_text = """
🛠️ Панель администратора

👥 Пользователи:
• Всего пользователей: {total_users}
• Активных: {active_users}
• Подписаны на бота: {bot_subscribers}
• Подписаны на оба канала: {channel_subscribers}
• Всего баллов в системе: {total_points}

🎁 Награды:
• Всего наград: {total_rewards}
• Активных: {active_rewards}
• Общая стоимость: {total_cost} баллов

📊 Транзакции:
• Всего транзакций: {total_transactions}
• Общее движение баллов: {total_points_movement}

⚡ Команды администратора:
/admin_users - Список пользователей
/admin_user <id> - Информация о пользователе
/admin_add_points - Начислить баллы
/admin_stats - Подробная статистика
        """.format(
            total_users=user_stats['total_users'],
            active_users=user_stats['active_users'],
            bot_subscribers=user_stats['bot_subscribers'],
            channel_subscribers=user_stats['channel_subscribers'],
            total_points=user_stats['total_points'],
            total_rewards=system_stats['rewards']['total'],
            active_rewards=system_stats['rewards']['active'],
            total_cost=system_stats['rewards']['total_cost'],
            total_transactions=system_stats['transactions']['total'],
            total_points_movement=system_stats['transactions']['total_points']
        )
        
        await message.answer(admin_text)
        
    except Exception as e:
        logger.error(f"❌ Error in admin panel handler: {e}")
        await message.answer("❌ Произошла ошибка при загрузке панели администратора")

@router.message(Command("admin_stats"))
async def admin_stats_handler(message: Message):
    """Show detailed statistics"""
    if not await check_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
        
    try:
        user_stats = AdminService.get_user_stats()
        system_stats = AdminService.get_system_stats()
        
        stats_text = """
📈 Детальная статистика

👥 Пользователи:
• Всего: {total_users}
• Активных: {active_users}
• Подписаны на бота: {bot_subscribers}
• Подписаны на оба канала: {channel_subscribers}
• Всего баллов: {total_points}

🎁 Награды:
• Всего: {total_rewards}
• Активных: {active_rewards}
• Общая стоимость: {total_cost}

📊 Транзакции:
• Всего: {total_transactions}
• Движение баллов: {total_points_movement}

📅 Активность за 7 дней:
{recent_activities}
        """.format(
            total_users=user_stats['total_users'],
            active_users=user_stats['active_users'],
            bot_subscribers=user_stats['bot_subscribers'],
            channel_subscribers=user_stats['channel_subscribers'],
            total_points=user_stats['total_points'],
            total_rewards=system_stats['rewards']['total'],
            active_rewards=system_stats['rewards']['active'],
            total_cost=system_stats['rewards']['total_cost'],
            total_transactions=system_stats['transactions']['total'],
            total_points_movement=system_stats['transactions']['total_points'],
            recent_activities="\n".join([f"• {activity}: {count}" for activity, count in system_stats['recent_activities'].items()]) if system_stats['recent_activities'] else "• Нет данных об активностях"
        )
        
        await message.answer(stats_text)
        
    except Exception as e:
        logger.error(f"❌ Error in admin stats handler: {e}")
        await message.answer("❌ Произошла ошибка при получении статистики")

@router.message(Command("admin_users"))
async def admin_users_handler(message: Message, command: CommandObject = None):
    """Show users list"""
    if not await check_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
        
    try:
        page = 1
        if command and command.args:
            try:
                page = int(command.args)
            except ValueError:
                await message.answer("❌ Неверный номер страницы.")
                return
        
        limit = 10
        offset = (page - 1) * limit
        
        users = AdminService.get_all_users(limit=limit, offset=offset)
        total_users = AdminService.get_users_count()
        total_pages = (total_users + limit - 1) // limit
        
        if not users:
            await message.answer("📭 Пользователи не найдены.")
            return
        
        users_text = f"👥 Список пользователей (страница {page}/{total_pages})\n\n"
        
        for i, user in enumerate(users, offset + 1):
            telegram_id, username, first_name, last_name, role, points, is_active, bot_sub, ch1_sub, ch2_sub, created_at = user
            
            users_text += f"{i}. [{telegram_id}] {first_name} {last_name or ''}\n"
            users_text += f"   @{username or 'нет'}\n"
            users_text += f"   Роль: {role} | Баллы: {points}\n"
            users_text += f"   Бот:{'✅' if bot_sub else '❌'} Канал1:{'✅' if ch1_sub else '❌'} Канал2:{'✅' if ch2_sub else '❌'}\n"
            users_text += f"   Дата: {created_at.strftime('%d.%m.%Y')}\n"
            users_text += "   ─────────────────\n"
        
        users_text += f"\nИспользуйте: /admin_users <номер_страницы>"
        
        await message.answer(users_text)
        
    except Exception as e:
        logger.error(f"❌ Error in admin users handler: {e}")
        await message.answer("❌ Произошла ошибка при получении списка пользователей")

@router.message(Command("admin_user"))
async def admin_user_handler(message: Message, command: CommandObject = None):
    """Show user details"""
    if not await check_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
        
    try:
        if not command or not command.args:
            await message.answer("❌ Укажите ID пользователя: /admin_user <user_id>")
            return
        
        try:
            user_id = int(command.args)
        except ValueError:
            await message.answer("❌ Неверный формат ID пользователя.")
            return
        
        user = UserService.get_user(user_id)
        
        if not user:
            await message.answer("❌ Пользователь не найден.")
            return
        
        (db_id, telegram_id, username, first_name, last_name, 
         role, points, referral_code, referred_by, is_active,
         bot_sub, ch1_sub, ch2_sub, welcome_given, created_at) = user
        
        # Get user transactions
        transactions = PointsService.get_user_transactions(user_id, limit=5)
        
        user_text = f"""
👤 *Информация о пользователе*

🆔 ID: {telegram_id}
👤 Имя: {first_name} {last_name or ''}
📛 Username: @{username or 'нет'}
🎭 Роль: {role}
💰 Баллы: {points}
🔗 Реф. код: {referral_code or 'нет'}
👥 Приглашен: {f'пользователем {referred_by}' if referred_by else 'нет'}

📊 *Статусы:*
• Активен: {'✅' if is_active else '❌'}
• Подписан на бота: {'✅' if bot_sub else '❌'}
• Канал 1: {'✅' if ch1_sub else '❌'}
• Канал 2: {'✅' if ch2_sub else '❌'}
• Приветственные баллы: {'✅' if welcome_given else '❌'}

📅 Регистрация: {created_at.strftime('%d.%m.%Y %H:%M')}

💳 *Последние транзакции:*
"""
        
        if transactions:
            for trans in transactions:
                trans_type, points_change, description, trans_date = trans
                sign = "+" if points_change > 0 else ""
                user_text += f"• {trans_date.strftime('%d.%m %H:%M')}: {sign}{points_change} - {trans_type}\n"
        else:
            user_text += "• Нет транзакций\n"
        
        user_text += f"\n⚡ Команды:\n/add_points_{user_id} - Начислить баллы"
        
        await message.answer(user_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Error in admin user handler: {e}")
        await message.answer("❌ Произошла ошибка при получении информации о пользователе")

@router.message(F.text.startswith('/add_points_'))
async def quick_add_points_handler(message: Message):
    """Quick add points using command format /add_points_123_50"""
    if not await check_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
        
    try:
        command_parts = message.text.split('_')
        
        if len(command_parts) < 3:
            await message.answer("❌ Неверный формат. Используйте: /add_points_<user_id>_<points>")
            return
        
        try:
            user_id = int(command_parts[2])
            points = int(command_parts[3]) if len(command_parts) > 3 else 0
        except (ValueError, IndexError):
            await message.answer("❌ Неверный формат чисел. Используйте: /add_points_<user_id>_<points>")
            return
        
        if points <= 0:
            await message.answer("❌ Введите положительное количество баллов.")
            return
        
        # Add points to user
        success, result = AdminService.add_points_to_user(user_id, points, "Быстрое начисление через команду")
        
        if success:
            user = UserService.get_user(user_id)
            user_name = f"{user[3]} {user[4] or ''}" if user else f"ID {user_id}"
            await message.answer(f"✅ Быстрое начисление баллов!\n\n👤 {user_name}\n💰 +{points} баллов\n\n{result}")
        else:
            await message.answer(f"❌ {result}")
            
    except Exception as e:
        logger.error(f"❌ Error in quick_add_points_handler: {e}")
        await message.answer("❌ Произошла ошибка при начислении баллов")
