import asyncio
import os
from dotenv import load_dotenv  # Импортируем библиотеку для чтения .env
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

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
