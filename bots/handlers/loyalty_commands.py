from aiogram import types
from aiogram.filters import Command
from config.loyalty_program import get_loyalty_rules_message
import logging

logger = logging.getLogger(__name__)

async def cmd_loyalty(message: types.Message):
    """Показывает правила программы лояльности"""
    try:
        rules_message = get_loyalty_rules_message()
        await message.answer(rules_message)
        logger.info(f"Пользователь {message.from_user.id} запросил правила лояльности")
    except Exception as e:
        logger.error(f"Ошибка показа правил лояльности: {e}")
        await message.answer("❌ Произошла ошибка при загрузке правил программы лояльности")

async def cmd_rewards(message: types.Message):
    """Показывает доступные награды"""
    try:
        from config.loyalty_program import LOYALTY_PROGRAM_RULES
        
        message_text = "🎁 Доступные награды за баллы:\n\n"
        
        for i, reward in enumerate(LOYALTY_PROGRAM_RULES["rewards"], 1):
            message_text += f"{i}. {reward}\n"
        
        message_text += "\n📊 Используйте /stats чтобы узнать свои баллы\n"
        message_text += "📋 Используйте /loyalty чтобы узнать полные правила"
        
        await message.answer(message_text)
        logger.info(f"Пользователь {message.from_user.id} запросил список наград")
        
    except Exception as e:
        logger.error(f"Ошибка показа наград: {e}")
        await message.answer("❌ Произошла ошибка при загрузке списка наград")
