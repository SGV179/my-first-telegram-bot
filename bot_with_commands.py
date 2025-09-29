import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, ChatMemberUpdatedFilter
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database.connections import create_tables
from bots.handlers.channel_handlers_fixed import handle_chat_member_update
from bots.handlers.user_commands import cmd_stats, cmd_channels
from config.settings import settings

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Создаем объекты бота и диспетчера
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Регистрируем обработчики
dp.chat_member.register(handle_chat_member_update)
dp.message.register(cmd_stats, Command("stats"))
dp.message.register(cmd_channels, Command("channels"))

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    await message.answer(
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я бот для администрирования каналов:\n"
        f"• @golden_square_1\n"
        f"• @golden_asset_1\n\n"
        f"📊 Используй команды:\n"
        f"/stats - твоя статистика\n"
        f"/channels - список каналов\n\n"
        f"Я отслеживаю активность в каналах и начисляю баллы! 🎁"
    )
    logger.info(f"Пользователь {user.id} запустил бота")

# Главная функция для запуска бота
async def main():
    create_tables()
    logger.info("✅ База данных инициализирована")
    logger.info("🚀 Бот запускается...")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
