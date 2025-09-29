import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.rewards_service import RewardsService
from app.services.points_service import PointsService
from app.services.file_service import FileService

logger = logging.getLogger(__name__)

router = Router()

class RewardStates(StatesGroup):
    waiting_for_reward_title = State()
    waiting_for_reward_description = State()
    waiting_for_reward_cost = State()

@router.message(Command("rewards"))
async def rewards_handler(message: Message):
    """Show available rewards"""
    try:
        user_id = message.from_user.id
        rewards = RewardsService.get_all_rewards()
        
        if not rewards:
            await message.answer("🎁 На данный момент нет доступных наград.")
            return
        
        rewards_text = "🎁 Доступные награды:\n\n"
        
        for reward in rewards:
            reward_id, title, description, cost_points, pdf_file_id = reward
            rewards_text += f"🏆 {title}\n"
            rewards_text += f"📝 {description}\n"
            rewards_text += f"💰 Стоимость: {cost_points} баллов\n"
            
            if pdf_file_id:
                rewards_text += f"📄 Файл: PDF документ\n"
            
            rewards_text += f"🛒 Для покупки используйте: /buy_{reward_id}\n"
            rewards_text += "─" * 30 + "\n"
        
        user_points = PointsService.get_user_points(user_id)
        rewards_text += f"\n💰 Ваш баланс: {user_points} баллов"
        rewards_text += f"\n\n📋 Ваши покупки: /my_rewards"
        
        await message.answer(rewards_text)
        
    except Exception as e:
        logger.error(f"❌ Error in rewards handler: {e}")
        await message.answer("❌ Произошла ошибка при получении списка наград")

@router.message(Command("my_rewards"))
async def my_rewards_handler(message: Message):
    """Show user's purchased rewards"""
    try:
        user_id = message.from_user.id
        user_rewards = RewardsService.get_user_rewards(user_id)
        
        if not user_rewards:
            await message.answer("📦 У вас пока нет купленных наград.")
            return
        
        rewards_text = "📦 Ваши купленные награды:\n\n"
        
        for i, reward in enumerate(user_rewards, 1):
            title, description, points_spent, purchased_at = reward
            rewards_text += f"{i}. 🏆 {title}\n"
            if description:
                rewards_text += f"   📝 {description}\n"
            rewards_text += f"   💰 Потрачено: {points_spent} баллов\n"
            rewards_text += f"   📅 Дата: {purchased_at.strftime('%d.%m.%Y %H:%M')}\n"
            rewards_text += "─" * 30 + "\n"
        
        await message.answer(rewards_text)
        
    except Exception as e:
        logger.error(f"❌ Error in my_rewards handler: {e}")
        await message.answer("❌ Произошла ошибка при получении ваших наград")

@router.message(F.text.startswith('/buy_'))
async def buy_reward_handler(message: Message):
    """Handle reward purchase and send PDF"""
    try:
        user_id = message.from_user.id
        command = message.text.split('_')
        
        if len(command) < 2:
            await message.answer("❌ Неверный формат команды. Используйте: /buy_1")
            return
        
        try:
            reward_id = int(command[1])
        except ValueError:
            await message.answer("❌ Неверный ID награды.")
            return
        
        # Purchase reward
        success, result, pdf_file_id = await RewardsService.purchase_reward(message.bot, user_id, reward_id)
        
        if success:
            response_text = f"🎉 Поздравляем! Вы успешно приобрели награду: {result}"
            
            if pdf_file_id:
                # Try to send PDF file
                pdf_sent = await FileService.send_pdf_to_user(
                    message.bot,
                    user_id,
                    pdf_file_id,
                    f"🎁 Ваша награда: {result}"
                )
                
                if pdf_sent:
                    response_text += f"\n📄 Файл отправлен! Проверьте свои сообщения."
                else:
                    response_text += f"\n⚠️ Файл временно недоступен. Свяжитесь с администратором."
            else:
                response_text += f"\n📞 Для получения награды свяжитесь с администратором."
            
            user_points = PointsService.get_user_points(user_id)
            response_text += f"\n\n💰 Ваш текущий баланс: {user_points} баллов"
            
            await message.answer(response_text)
        else:
            await message.answer(f"❌ {result}")
            
    except Exception as e:
        logger.error(f"❌ Error in buy_reward handler: {e}")
        await message.answer("❌ Произошла ошибка при покупке награды")

# Админ команды для управления наградами
@router.message(Command("add_reward"))
async def add_reward_start(message: Message, state: FSMContext):
    """Start adding new reward (admin only)"""
    try:
        # TODO: Добавить проверку на админа
        await message.answer("🏆 Добавление новой награды:\n\nВведите название награды:")
        await state.set_state(RewardStates.waiting_for_reward_title)
        
    except Exception as e:
        logger.error(f"❌ Error in add_reward_start: {e}")
        await message.answer("❌ Произошла ошибка")

@router.message(RewardStates.waiting_for_reward_title)
async def process_reward_title(message: Message, state: FSMContext):
    """Process reward title"""
    try:
        await state.update_data(title=message.text)
        await message.answer("📝 Введите описание награды:")
        await state.set_state(RewardStates.waiting_for_reward_description)
        
    except Exception as e:
        logger.error(f"❌ Error in process_reward_title: {e}")
        await message.answer("❌ Произошла ошибка")

@router.message(RewardStates.waiting_for_reward_description)
async def process_reward_description(message: Message, state: FSMContext):
    """Process reward description"""
    try:
        await state.update_data(description=message.text)
        await message.answer("💰 Введите стоимость награды в баллах:")
        await state.set_state(RewardStates.waiting_for_reward_cost)
        
    except Exception as e:
        logger.error(f"❌ Error in process_reward_description: {e}")
        await message.answer("❌ Произошла ошибка")

@router.message(RewardStates.waiting_for_reward_cost)
async def process_reward_cost(message: Message, state: FSMContext):
    """Process reward cost and create reward"""
    try:
        try:
            cost_points = int(message.text)
        except ValueError:
            await message.answer("❌ Введите корректное число для стоимости.")
            return
        
        data = await state.get_data()
        reward_id = RewardsService.create_reward(
            title=data['title'],
            description=data['description'],
            cost_points=cost_points
        )
        
        if reward_id:
            await message.answer(f"✅ Награда успешно создана! ID: {reward_id}")
        else:
            await message.answer("❌ Ошибка при создании награды.")
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"❌ Error in process_reward_cost: {e}")
        await message.answer("❌ Произошла ошибка при создании награды")
        await state.clear()
