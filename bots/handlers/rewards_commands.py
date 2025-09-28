from aiogram import types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.rewards_service import RewardsService
import logging

logger = logging.getLogger(__name__)

async def cmd_shop(message: types.Message):
    """Показывает магазин наград"""
    try:
        rewards_service = RewardsService()
        rewards = rewards_service.get_available_rewards()
        user_balance = rewards_service.get_user_balance(message.from_user.id)
        
        if not rewards:
            await message.answer("🛍️ Магазин наград пуст. Загляните позже!")
            return
        
        builder = InlineKeyboardBuilder()
        
        message_text = f"🛍️ Магазин наград\n\n💰 Ваш баланс: {user_balance} баллов\n\n"
        
        for reward in rewards:
            message_text += f"🎁 <b>{reward.name}</b>\n"
            message_text += f"📝 {reward.description}\n"
            message_text += f"💰 Стоимость: {reward.cost} баллов\n\n"
            
            builder.button(
                text=f"🛒 {reward.name} - {reward.cost} баллов", 
                callback_data=f"buy_reward_{reward.id}"
            )
        
        builder.button(text="📊 Мой баланс", callback_data="my_balance")
        builder.button(text="📋 История обменов", callback_data="redemption_history")
        builder.adjust(1)  # По одной кнопке в ряд
        
        await message.answer(message_text, reply_markup=builder.as_markup())
        logger.info(f"Пользователь {message.from_user.id} открыл магазин наград")
        
    except Exception as e:
        logger.error(f"Ошибка показа магазина: {e}")
        await message.answer("❌ Произошла ошибка при загрузке магазина")

async def cmd_balance(message: types.Message):
    """Показывает баланс пользователя"""
    try:
        rewards_service = RewardsService()
        balance = rewards_service.get_user_balance(message.from_user.id)
        
        if balance == 0:
            await message.answer(
                "💰 Ваш баланс: 0 баллов\n\n"
                "🎯 Чтобы зарабатывать баллы:\n"
                "1. Подпишитесь на бота и оба канала\n"
                "2. Будьте активны в каналах\n"
                "3. Получайте баллы за лайки, комментарии и репосты!\n\n"
                "📋 Используйте /loyalty чтобы узнать подробности"
            )
        else:
            await message.answer(f"💰 Ваш баланс: {balance} баллов\n\n🛍️ Используйте /shop чтобы обменять баллы на награды!")
        
        logger.info(f"Пользователь {message.from_user.id} запросил баланс")
        
    except Exception as e:
        logger.error(f"Ошибка показа баланса: {e}")
        await message.answer("❌ Произошла ошибка при получении баланса")

async def handle_rewards_callback(callback: types.CallbackQuery):
    """Обрабатывает callback-запросы системы наград"""
    try:
        data = callback.data
        
        if data == "my_balance":
            await cmd_balance(callback.message)
            
        elif data == "redemption_history":
            await show_redemption_history(callback)
            
        elif data.startswith("buy_reward_"):
            reward_id = int(data.split("_")[2])
            await buy_reward(callback, reward_id)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка обработки callback наград: {e}")
        await callback.answer("❌ Произошла ошибка")

async def show_redemption_history(callback: types.CallbackQuery):
    """Показывает историю обменов"""
    try:
        rewards_service = RewardsService()
        redemptions = rewards_service.get_user_redemptions(callback.from_user.id)
        
        if not redemptions:
            await callback.message.answer("📋 У вас еще не было обменов баллов на награды")
            return
        
        message_text = "📋 История ваших обменов:\n\n"
        
        for redemption in redemptions:
            status_emoji = "⏳" if redemption.status == 'pending' else "✅"
            message_text += f"{status_emoji} {redemption.reward.name}\n"
            message_text += f"   💰 {redemption.reward.cost} баллов\n"
            message_text += f"   📅 {redemption.redeemed_at.strftime('%d.%m.%Y %H:%M')}\n"
            message_text += f"   📊 Статус: {redemption.status}\n\n"
        
        await callback.message.answer(message_text)
        
    except Exception as e:
        logger.error(f"Ошибка показа истории обменов: {e}")
        await callback.message.answer("❌ Произошла ошибка при загрузке истории")

async def buy_reward(callback: types.CallbackQuery, reward_id: int):
    """Обрабатывает покупку награды"""
    try:
        rewards_service = RewardsService()
        result = rewards_service.redeem_reward(callback.from_user.id, reward_id)
        
        if result["success"]:
            # Показываем успешное сообщение
            await callback.message.answer(result["message"])
            
            # Обновляем сообщение с магазином
            builder = InlineKeyboardBuilder()
            builder.button(text="🛍️ Продолжить покупки", callback_data="back_to_shop")
            builder.button(text="📊 Мой баланс", callback_data="my_balance")
            
            await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        else:
            await callback.message.answer(result["message"])
            
    except Exception as e:
        logger.error(f"Ошибка покупки награды: {e}")
        await callback.message.answer("❌ Произошла ошибка при покупке награды")
