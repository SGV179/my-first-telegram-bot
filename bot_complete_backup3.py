import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Reward

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота
API_TOKEN = '8477241287:AAGXKwYGBmMJ9LIZJwAUXFA_fL89mrSrCKc'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Настройка базы данных
engine = create_engine('sqlite:///bot_database.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db_session = DBSession()

# Создание таблиц
Base.metadata.create_all(engine)

# Состояния для FSM
class AdminStates(StatesGroup):
    waiting_for_reward_file = State()
    waiting_for_reward_title = State()
    waiting_for_reward_points = State()

# Клавиатуры
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Мой профиль'))
    keyboard.add(KeyboardButton('Каталог наград'))
    keyboard.add(KeyboardButton('Админ панель'))
    return keyboard

def get_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Добавить награду'))
    keyboard.add(KeyboardButton('Список наград'))
    keyboard.add(KeyboardButton('На главную'))
    return keyboard

def get_rewards_keyboard():
    keyboard = InlineKeyboardMarkup()
    rewards = db_session.query(Reward).all()
    
    # Убираем дубликаты по названию
    seen_titles = set()
    unique_rewards = []
    
    for reward in rewards:
        if reward.title not in seen_titles:
            seen_titles.add(reward.title)
            unique_rewards.append(reward)
    
    for reward in unique_rewards:
        button_text = f"{reward.title} - {reward.points_cost} баллов"
        if len(button_text) > 50:  # Ограничиваем длину текста
            button_text = reward.title[:47] + "..."
        
        keyboard.add(InlineKeyboardButton(
            button_text,
            callback_data=f"reward_{reward.id}"
        ))
    return keyboard

# Инициализация начальных наград (исправленная)
def initialize_rewards():
    # Проверяем, есть ли уже награды в базе
    existing_rewards = db_session.query(Reward).count()
    if existing_rewards == 0:
        initial_rewards = [
            {
                "title": "Гайд. Как выбрать планировку квартиры?",
                "points_cost": 50
            },
            {
                "title": "ТОП 10 требований покупателей квартир в премиум-классе в 2025 году",
                "points_cost": 30
            },
            {
                "title": "ТОП 10 требований покупателей квартир в комфорт-классе в 2025 году", 
                "points_cost": 30
            },
            {
                "title": "Чек-лист. Как выбрать 1-комнатную квартиру для жизни?",
                "points_cost": 30
            },
            {
                "title": "Чек-лист. Как выбрать 1-комнатную квартиру для аренды?",
                "points_cost": 30
            },
            {
                "title": "Чек-лист. Как выбрать 2-комнатную квартиру для жизни?",
                "points_cost": 30
            },
            {
                "title": "Чек-лист. Как выбрать 2-комнатную квартиру для аренды?",
                "points_cost": 30
            }
        ]
        
        for reward_data in initial_rewards:
            # Проверяем, нет ли уже такой награды
            existing = db_session.query(Reward).filter_by(title=reward_data["title"]).first()
            if not existing:
                reward = Reward(
                    title=reward_data["title"],
                    points_cost=reward_data["points_cost"]
                )
                db_session.add(reward)
        
        db_session.commit()
        logging.info("Initial rewards checked/added to database")

# Обработчики команд
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(
        "Добро пожаловать в бот!\n\n"
        "Здесь вы можете получать полезные материалы за баллы.",
        reply_markup=get_main_keyboard()
    )

@dp.message_handler(lambda message: message.text == 'На главную')
async def cmd_main_menu(message: types.Message):
    await message.answer("Главное меню:", reply_markup=get_main_keyboard())

@dp.message_handler(lambda message: message.text == 'Мой профиль')
async def cmd_profile(message: types.Message):
    # Заглушка для профиля
    await message.answer(
        "Ваш профиль:\n"
        "Баллы: 100\n\n"
        "Здесь будет отображаться ваше текущее количество баллов."
    )

@dp.message_handler(lambda message: message.text == 'Каталог наград')
async def cmd_rewards_catalog(message: types.Message):
    rewards = db_session.query(Reward).all()
    if not rewards:
        await message.answer("Награды пока не добавлены.")
        return
    
    # Убираем дубликаты
    seen_titles = set()
    unique_rewards = []
    
    for reward in rewards:
        if reward.title not in seen_titles:
            seen_titles.add(reward.title)
            unique_rewards.append(reward)
    
    text = "🏆 Каталог наград:\n\n"
    for reward in unique_rewards:
        status = "✅ Доступно" if reward.file_id else "❌ Файл не загружен"
        text += f"• {reward.title} - {reward.points_cost} баллов {status}\n"
    
    text += "\nВыберите награду для получения:"
    await message.answer(text, reply_markup=get_rewards_keyboard())

@dp.message_handler(lambda message: message.text == 'Админ панель')
async def cmd_admin_panel(message: types.Message):
    # Упрощенная проверка - разрешаем всем для тестирования
    # В реальном боте здесь должна быть проверка user_id
    await message.answer(
        "👨‍💻 Админ панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )

@dp.message_handler(lambda message: message.text == 'Добавить награду')
async def cmd_add_reward(message: types.Message):
    await message.answer("Пожалуйста, отправьте PDF файл для новой награды:")
    await AdminStates.waiting_for_reward_file.set()

@dp.message_handler(lambda message: message.text == 'Список наград')
async def cmd_rewards_list(message: types.Message):
    rewards = db_session.query(Reward).all()
    if not rewards:
        await message.answer("Награды пока не добавлены.")
        return
    
    text = "📋 Список наград:\n\n"
    for reward in rewards:
        status = "✅ Файл загружен" if reward.file_id else "❌ Файл отсутствует"
        text += f"• {reward.title}\n  Цена: {reward.points_cost} баллов\n  Статус: {status}\n\n"
    
    await message.answer(text)

# Обработка callback'ов для наград
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('reward_'))
async def process_reward_callback(callback_query: types.CallbackQuery):
    reward_id = int(callback_query.data.split('_')[1])
    reward = db_session.query(Reward).filter(Reward.id == reward_id).first()
    
    if not reward:
        await callback_query.answer("Награда не найдена")
        return
    
    if not reward.file_id:
        await callback_query.answer("Файл для этой награды еще не загружен")
        return
    
    # Здесь будет логика списания баллов
    # Пока просто отправляем файл
    try:
        await bot.send_document(
            callback_query.from_user.id,
            reward.file_id,
            caption=f"🎉 Поздравляем! Вы получили: {reward.title}"
        )
        await callback_query.answer("Награда отправлена!")
    except Exception as e:
        await callback_query.answer("Ошибка при отправке файла")
        logging.error(f"Error sending file: {e}")

# Обработка загрузки файлов для наград
@dp.message_handler(state=AdminStates.waiting_for_reward_file, content_types=types.ContentType.DOCUMENT)
async def process_reward_file(message: types.Message, state: FSMContext):
    if not message.document.mime_type == 'application/pdf':
        await message.answer("Пожалуйста, отправьте файл в формате PDF.")
        return
    
    async with state.proxy() as data:
        data['file_id'] = message.document.file_id
        data['file_name'] = message.document.file_name
    
    await message.answer("Теперь введите название награды:")
    await AdminStates.waiting_for_reward_title.set()

@dp.message_handler(state=AdminStates.waiting_for_reward_title)
async def process_reward_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = message.text
    
    await message.answer("Теперь введите стоимость награды в баллах:")
    await AdminStates.waiting_for_reward_points.set()

@dp.message_handler(state=AdminStates.waiting_for_reward_points)
async def process_reward_points(message: types.Message, state: FSMContext):
    try:
        points = int(message.text)
        if points <= 0:
            await message.answer("Стоимость должна быть положительным числом. Попробуйте еще раз:")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите число. Попробуйте еще раз:")
        return
    
    async with state.proxy() as data:
        # Создаем новую награду
        reward = Reward(
            title=data['title'],
            file_id=data['file_id'],
            file_name=data['file_name'],
            points_cost=points
        )
        
        db_session.add(reward)
        db_session.commit()
    
    await message.answer(f"Награда '{data['title']}' успешно добавлена за {points} баллов!")
    await state.finish()

if __name__ == '__main__':
    # Инициализируем начальные награды
    initialize_rewards()
    
    # Запускаем бота
    logging.info("Bot starting...")
    executor.start_polling(dp, skip_updates=True)
