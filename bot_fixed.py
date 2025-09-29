import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, ChatMemberUpdatedFilter
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database.connections import create_tables
from bots.handlers.channel_handlers_fixed import handle_chat_member_update
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

# Регистрируем обработчик подписок/отписок в каналах
dp.chat_member.register(handle_chat_member_update)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    await message.answer(
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я бот для администрирования каналов.\n"
        f"Отслеживаю подписки в каналах и начисляю баллы!"
    )
    logger.info(f"Пользователь {user.id} запустил бота")

# Главная функция для запуска бота
async def main():
    # Создаем таблицы в базе данных
    create_tables()
    logger.info("✅ База данных инициализирована")
    
    # Запускаем бота
    logger.info("🚀 Бот запускается...")
    logger.info(f"📊 Отслеживаем каналы: {settings.CHANNELS}")
    
    await dp.start_polling(bot)

# Запуск программы
if __name__ == "__main__":
    asyncio.run(main())
