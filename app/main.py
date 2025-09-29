import asyncio
import logging
from aiogram import Bot, Dispatcher
from app.config.config import config
from app.database.db_connection import db
from app.utils.logger import logger

async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    try:
        # Test database connection
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        logger.info(f"✅ Database version: {db_version[0]}")
        cursor.close()

        # Test bot connection
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot started successfully: @{bot_info.username}")

        # Start polling
        logger.info("🚀 Bot is starting...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
    finally:
        await bot.session.close()
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
