import asyncio
import os
from dotenv import load_dotenv  # Импортируем библиотеку для чтения .env
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

#!/usr/bin/env python3
"""
Главный файл Telegram бота с интеграцией базы данных
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.database import init_database
from services.bot_service import BotService

# 🔐 Настройки бота
BOT_TOKEN = "8477241287:AAGXKwYGBmMJ9LIZJwAUXFA_fL89mrSrCKc"  # ⬅️ ЗАМЕНИТЕ НА РЕАЛЬНЫЙ ТОКЕН

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
init_database()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    bot_service = BotService()
    
    try:
        user = update.effective_user
        chat = update.effective_chat
        
        # Регистрируем пользователя в базе данных
        db_user = bot_service.register_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Отслеживаем событие старта
        bot_service.track_user_event(
            user_id=db_user.id,
            event_type="start_command"
        )
        
        welcome_text = f"""
👋 Привет, {user.first_name}!

✅ Ты зарегистрирован в системе!
📊 Твой ID в базе: {db_user.id}

Доступные команды:
/start - начать работу
/profile - посмотреть профиль
/stats - статистика
        """
        
        await update.message.reply_text(welcome_text)
        
    except Exception as e:
        logger.error(f"Ошибка в start_command: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
    
    finally:
        bot_service.close_connection()

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /profile"""
    bot_service = BotService()
    
    try:
        user = update.effective_user
        
        # Получаем пользователя из базы
        db_user = bot_service.register_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Отслеживаем просмотр профиля
        bot_service.track_user_event(
            user_id=db_user.id,
            event_type="view_profile"
        )
        
        profile_text = f"""
📊 Твой профиль:

👤 Имя: {user.first_name} {user.last_name or ''}
🔗 Username: @{user.username or 'не указан'}
🆔 Telegram ID: {user.id}
📈 ID в базе: {db_user.id}
        """
        
        await update.message.reply_text(profile_text)
        
    except Exception as e:
        logger.error(f"Ошибка в profile_command: {e}")
        await update.message.reply_text("❌ Произошла ошибка при загрузке профиля.")
    
    finally:
        bot_service.close_connection()

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats"""
    bot_service = BotService()
    
    try:
        user = update.effective_user
        
        # Получаем пользователя из базы
        db_user = bot_service.register_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Получаем статистику (заглушка - можно расширить)
        stats = bot_service.get_user_stats(db_user.id)
        
        # Отслеживаем запрос статистики
        bot_service.track_user_event(
            user_id=db_user.id,
            event_type="view_stats"
        )
        
        stats_text = f"""
📈 Твоя статистика:

👤 Пользователь: {db_user.id}
📊 Событий записано: {stats['events_count']}
🔄 База данных: ✅ подключена
        """
        
        await update.message.reply_text(stats_text)
        
    except Exception as e:
        logger.error(f"Ошибка в stats_command: {e}")
        await update.message.reply_text("❌ Произошла ошибка при загрузке статистики.")
    
    finally:
        bot_service.close_connection()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обычных сообщений"""
    bot_service = BotService()
    
    try:
        user = update.effective_user
        message_text = update.message.text
        
        # Получаем пользователя из базы
        db_user = bot_service.register_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Отслеживаем сообщение
        bot_service.track_user_event(
            user_id=db_user.id,
            event_type="user_message",
            event_data={"text_length": len(message_text)}
        )
        
        response_text = f"""
💬 Сообщение получено и записано в базу!

📝 Длина сообщения: {len(message_text)} символов
🆔 Ваш ID: {db_user.id}
        """
        
        await update.message.reply_text(response_text)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")
    
    finally:
        bot_service.close_connection()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

def main():
    """Основная функция запуска бота"""
    print("🤖 Запуск бота с интеграцией базы данных...")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    print("✅ Бот запущен. Ожидаем сообщения...")
    application.run_polling()

if __name__ == "__main__":
    main()

# Загружаем переменные из файла .env
load_dotenv()

# Теперь токен безопасно берется из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Проверяем, что токен загрузился
if not BOT_TOKEN:
    print("Ошибка: Токен бота не найден! Проверьте файл .env")
    exit(1)

# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я твой первый бот, написанный на aiogram! 👋")

# Обработчик всех текстовых сообщений (будет эхом повторять текст)
@dp.message()
async def echo_message(message: types.Message):
    await message.answer(message.text)

# Главная функция для запуска бота
async def main():
    print("Бот запускается...")
    await dp.start_polling(bot)

# Запуск программы
if __name__ == "__main__":
    asyncio.run(main())
