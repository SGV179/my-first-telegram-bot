import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.activity_service import ActivityService
from app.services.user_service import UserService
from app.config.config import config

logger = logging.getLogger(__name__)

router = Router()

class ManualActivityStates(StatesGroup):
    waiting_for_activity_type = State()
    waiting_for_activity_description = State()

@router.message(Command("add_like"))
async def add_like_handler(message: Message):
    """Manually add like activity"""
    try:
        user_id = message.from_user.id
        
        success = ActivityService.track_activity(
            user_id,
            'like',
            config.CHANNEL_1_ID,
            description="Ручное добавление лайка"
        )
        
        if success:
            await message.answer("✅ Лайк успешно добавлен! Проверьте /activities")
        else:
            await message.answer("❌ Ошибка при добавлении лайка")
            
    except Exception as e:
        logger.error(f"❌ Error in add_like handler: {e}")
        await message.answer("❌ Произошла ошибка")

@router.message(Command("add_comment"))
async def add_comment_handler(message: Message):
    """Manually add comment activity"""
    try:
        user_id = message.from_user.id
        
        success = ActivityService.track_activity(
            user_id,
            'comment',
            config.CHANNEL_1_ID,
            description="Ручное добавление комментария"
        )
        
        if success:
            await message.answer("✅ Комментарий успешно добавлен! Проверьте /activities")
        else:
            await message.answer("❌ Ошибка при добавлении комментария")
            
    except Exception as e:
        logger.error(f"❌ Error in add_comment handler: {e}")
        await message.answer("❌ Произошла ошибка")

@router.message(Command("add_repost"))
async def add_repost_handler(message: Message):
    """Manually add repost activity"""
    try:
        user_id = message.from_user.id
        
        success = ActivityService.track_activity(
            user_id,
            'repost',
            config.CHANNEL_1_ID,
            description="Ручное добавление репоста"
        )
        
        if success:
            await message.answer("✅ Репост успешно добавлен! Проверьте /activities")
        else:
            await message.answer("❌ Ошибка при добавлении репоста")
            
    except Exception as e:
        logger.error(f"❌ Error in add_repost handler: {e}")
        await message.answer("❌ Произошла ошибка")

@router.message(Command("add_button_click"))
async def add_button_click_handler(message: Message):
    """Manually add button click activity"""
    try:
        user_id = message.from_user.id
        
        success = ActivityService.track_activity(
            user_id,
            'button_click',
            config.CHANNEL_1_ID,
            description="Ручное добавление нажатия кнопки"
        )
        
        if success:
            await message.answer("✅ Нажатие кнопки успешно добавлено! Проверьте /activities")
        else:
            await message.answer("❌ Ошибка при добавлении нажатия кнопки")
            
    except Exception as e:
        logger.error(f"❌ Error in add_button_click handler: {e}")
        await message.answer("❌ Произошла ошибка")

@router.message(Command("quick_activities"))
async def quick_activities_handler(message: Message):
    """Show quick activity buttons"""
    quick_text = """
⚡ Быстрое добавление активностей:

/add_like - Добавить лайк (+1 балл)
/add_comment - Добавить комментарий (+5 баллов)  
/add_repost - Добавить репост (+3 балла)
/add_button_click - Добавить нажатие кнопки (+10 баллов)

/test_activity - Тест всех активностей
/activities - Показать историю активностей

📋 Для автоматического отслеживания:
1. Бот должен быть администратором в каналах
2. С правами на просмотр сообщений
3. Тогда лайки/комментарии будут отслеживаться автоматически
    """
    
    await message.answer(quick_text)
