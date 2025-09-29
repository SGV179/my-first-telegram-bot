import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config.config import config
from app.database.db_connection import db
from app.models.database_models import init_database
from app.services.user_service import UserService
from app.services.points_service import PointsService
from app.services.channel_service import ChannelService
from app.handlers.user_handlers import router as user_router
from app.utils.logger import logger

async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    try:
        # Test database connection and initialize tables
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        logger.info(f"✅ Database version: {db_version[0]}")
        cursor.close()

        # Initialize database tables
        init_database()
        logger.info("✅ Database tables initialized")

        # Test bot connection
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot started successfully: @{bot_info.username}")

        # Register handlers
        dp.message.register(start_handler, CommandStart())
        dp.include_router(user_router)

        # Start polling
        logger.info("🚀 Bot is starting...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
    finally:
        await bot.session.close()
        db.close()

async def start_handler(message: Message):
    """Handle /start command"""
    try:
        user = message.from_user
        logger.info(f"👤 User {user.id} started the bot")

        # Create or update user in database
        user_data = UserService.create_or_update_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

        if user_data:
            # Update bot subscription status
            UserService.update_subscription_status(
                telegram_id=user.id,
                bot_subscribed=True
            )

            # Check channel subscriptions
            subscription_result = await ChannelService.check_user_subscription(message.bot, user.id)
            
            welcome_text = f"""
👋 Добро пожаловать, {user.first_name}!

🤖 Я - бот для управления каналами и системой лояльности.

📊 Ваши баллы: {PointsService.get_user_points(user.id)}

📺 Статус подписки:
{config.CHANNEL_1}: {'✅' if subscription_result['channel_1'] else '❌'}
{config.CHANNEL_2}: {'✅' if subscription_result['channel_2'] else '❌'}

💡 Используйте команды:
/points - ваши баллы
/profile - ваш профиль
/check_subscription - проверить подписку
/rewards - доступные награды
/help - справка по командам
            """

            if subscription_result['welcome_points'] > 0:
                welcome_text += f"\n🎉 Вам начислено {subscription_result['welcome_points']} приветственных баллов!"
            elif not subscription_result['subscribed']:
                welcome_text += f"\n\n📋 Для получения приветственных баллов подпишитесь на оба канала выше!"

            await message.answer(welcome_text)
        else:
            await message.answer("❌ Произошла ошибка при регистрации. Попробуйте позже.")

    except Exception as e:
        logger.error(f"❌ Error in start handler: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")

if __name__ == "__main__":
    asyncio.run(main())
