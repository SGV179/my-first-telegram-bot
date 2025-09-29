import logging
from app.services.channel_service import ChannelService
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from app.services.user_service import UserService
from app.services.points_service import PointsService

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("points"))
async def points_handler(message: Message):
    """Show user points"""
    try:
        user_id = message.from_user.id
        points = PointsService.get_user_points(user_id)
        
        await message.answer(f"💰 Ваши баллы: {points}")
        
    except Exception as e:
        logger.error(f"❌ Error in points handler: {e}")
        await message.answer("❌ Произошла ошибка при получении баллов")

@router.message(Command("profile"))
async def profile_handler(message: Message):
    """Show user profile"""
    try:
        user_id = message.from_user.id
        user = UserService.get_user(user_id)
        
        if user:
            subscriptions = UserService.check_user_subscriptions(user_id)
            
            profile_text = f"""
👤 Ваш профиль:

🆔 ID: {user[1]}
👤 Имя: {user[3]} {user[4] or ''}
📛 Username: @{user[2] or 'не указан'}
🎭 Роль: {user[5]}
💰 Баллы: {user[6]}

📊 Подписки:
🤖 Бот: {'✅' if subscriptions and subscriptions['bot'] else '❌'}
📺 {user[12]}: {'✅' if subscriptions and subscriptions['channel_1'] else '❌'}
📺 {user[13]}: {'✅' if subscriptions and subscriptions['channel_2'] else '❌'}
            """
            
            await message.answer(profile_text)
        else:
            await message.answer("❌ Пользователь не найден")
            
    except Exception as e:
        logger.error(f"❌ Error in profile handler: {e}")
        await message.answer("❌ Произошла ошибка при получении профиля")

@router.message(Command("help"))
async def help_handler(message: Message):
    """Show help message"""
    help_text = """
🤖 Доступные команды:

/start - Начать работу с ботом
/points - Показать ваши баллы
/profile - Показать ваш профиль
/check_subscription - Проверить подписку на каналы
/rewards - Показать доступные награды
/help - Показать эту справку

💡 Система баллов:
• Подписка на оба канала: 30 баллов
• Комментарий: 5 баллов
• Репост: 3 балла
• Лайк: 1 балл
• Нажатие кнопки: 10 баллов
• Приглашение друга: 50 баллов

🎁 Накопленные баллы можно обменять на награды!
    """
    
    await message.answer(help_text)

@router.message(Command("check_subscription"))
async def check_subscription_handler(message: Message):
    """Check user subscription status"""
    try:
        user_id = message.from_user.id
        result = await ChannelService.require_subscription(message.bot, user_id)
        
        await message.answer(result)
        
    except Exception as e:
        logger.error(f"❌ Error in check_subscription handler: {e}")
        await message.answer("❌ Произошла ошибка при проверке подписки")
