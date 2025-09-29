import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from models import Base, Reward, User, Transaction

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
    waiting_for_reward_edit = State()
    waiting_for_reward_edit_points = State()

# Вспомогательные функции
def get_or_create_user(user_id, username=None, first_name=None, last_name=None):
    """Получает пользователя из базы или создает нового"""
    user = db_session.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        db_session.add(user)
        db_session.commit()
    return user

def get_user_balance(user_id):
    """Получает баланс пользователя"""
    user = db_session.query(User).filter(User.user_id == user_id).first()
    return user.points if user else 0

def create_transaction(user_id, reward_id, points_change, transaction_type):
    """Создает запись о транзакции"""
    user = db_session.query(User).filter(User.user_id == user_id).first()
    if user:
        transaction = Transaction(
            user_id=user.id,
            reward_id=reward_id,
            points_change=points_change,
            transaction_type=transaction_type
        )
        db_session.add(transaction)
        
        # Обновляем баланс пользователя
        user.points += points_change
        db_session.commit()
        return True
    return False

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
    keyboard.add(KeyboardButton('Управление наградами'))
    keyboard.add(KeyboardButton('На главную'))
    return keyboard

def get_rewards_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    rewards = db_session.query(Reward).all()
    user_balance = get_user_balance(user_id)
    
    # Берем только награды с загруженными файлами
    available_rewards = [r for r in rewards if r.file_id]
    
    for reward in available_rewards:
        can_afford = user_balance >= reward.points_cost
        status_icon = "✅" if can_afford else "❌"
        button_text = f"{status_icon} {reward.title} - {reward.points_cost} баллов"
        
        if len(button_text) > 50:
            button_text = f"{status_icon} {reward.title[:47]}..."
        
        callback_data = f"reward_{reward.id}" if can_afford else "not_enough_points"
        
        keyboard.add(InlineKeyboardButton(
            button_text,
            callback_data=callback_data
        ))
    return keyboard

def get_manage_rewards_keyboard():
    keyboard = InlineKeyboardMarkup()
    rewards = db_session.query(Reward).all()
    
    for reward in rewards:
        button_text = f"{reward.title}"
        if len(button_text) > 30:
            button_text = reward.title[:27] + "..."
        
        keyboard.row(
            InlineKeyboardButton(
                button_text,
                callback_data=f"view_reward_{reward.id}"
            ),
            InlineKeyboardButton(
                "✏️",
                callback_data=f"edit_reward_{reward.id}"
            ),
            InlineKeyboardButton(
                "❌", 
                callback_data=f"delete_reward_{reward.id}"
            )
        )
    
    keyboard.add(InlineKeyboardButton("Назад в админку", callback_data="back_to_admin"))
    return keyboard

# Очистка базы от дубликатов
def cleanup_duplicates():
    """Удаляет дубликаты наград по названию, оставляя только последнюю версию"""
    try:
        all_rewards = db_session.query(Reward).all()
        unique_titles = {}
        duplicates_to_delete = []
        
        for reward in all_rewards:
            if reward.title in unique_titles:
                duplicates_to_delete.append(reward.id)
            else:
                unique_titles[reward.title] = reward.id
        
        if duplicates_to_delete:
            for reward_id in duplicates_to_delete:
                reward_to_delete = db_session.query(Reward).filter(Reward.id == reward_id).first()
                if reward_to_delete:
                    db_session.delete(reward_to_delete)
            
            db_session.commit()
            logging.info(f"Removed {len(duplicates_to_delete)} duplicate rewards")
        else:
            logging.info("No duplicates found")
            
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")

# Инициализация начальных наград
def initialize_rewards():
    cleanup_duplicates()
    
    existing_rewards = db_session.query(Reward).count()
    if existing_rewards == 0:
        initial_rewards = [
            {"title": "Гайд. Как выбрать планировку квартиры?", "points_cost": 50},
            {"title": "ТОП 10 требований покупателей квартир в премиум-классе в 2025 году", "points_cost": 30},
            {"title": "ТОП 10 требований покупателей квартир в комфорт-классе в 2025 году", "points_cost": 30},
            {"title": "Чек-лист. Как выбрать 1-комнатную квартиру для жизни?", "points_cost": 30},
            {"title": "Чек-лист. Как выбрать 1-комнатную квартиру для аренды?", "points_cost": 30},
            {"title": "Чек-лист. Как выбрать 2-комнатную квартиру для жизни?", "points_cost": 30},
            {"title": "Чек-лист. Как выбрать 2-комнатную квартиру для аренды?", "points_cost": 30}
        ]
        
        for reward_data in initial_rewards:
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
    # Создаем/получаем пользователя
    user = get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    await message.answer(
        f"Добро пожаловать в бот, {message.from_user.first_name}!\n\n"
        "Здесь вы можете получать полезные материалы за баллы.",
        reply_markup=get_main_keyboard()
    )

@dp.message_handler(lambda message: message.text == 'На главную')
async def cmd_main_menu(message: types.Message):
    await message.answer("Главное меню:", reply_markup=get_main_keyboard())

@dp.message_handler(lambda message: message.text == 'Мой профиль')
async def cmd_profile(message: types.Message):
    user = get_or_create_user(message.from_user.id)
    await message.answer(
        f"👤 Ваш профиль:\n\n"
        f"Имя: {message.from_user.first_name or 'Не указано'}\n"
        f"Username: @{message.from_user.username or 'Не указан'}\n"
        f"Баланс: {user.points} баллов\n\n"
        f"Используйте баллы для получения полезных материалов!"
    )

@dp.message_handler(lambda message: message.text == 'Каталог наград')
async def cmd_rewards_catalog(message: types.Message):
    rewards = db_session.query(Reward).all()
    available_rewards = [r for r in rewards if r.file_id]
    user_balance = get_user_balance(message.from_user.id)
    
    if not available_rewards:
        await message.answer("Пока нет доступных наград. Файлы еще не загружены.")
        return
    
    text = f"🏆 Каталог наград (Ваш баланс: {user_balance} баллов):\n\n"
    for reward in available_rewards:
        can_afford = user_balance >= reward.points_cost
        status = "✅ Доступно" if can_afford else f"❌ Недостаточно баллов (нужно {reward.points_cost})"
        text += f"• {reward.title} - {reward.points_cost} баллов\n  {status}\n\n"
    
    text += "Выберите награду для получения:"
    await message.answer(text, reply_markup=get_rewards_keyboard(message.from_user.id))

@dp.message_handler(lambda message: message.text == 'Админ панель')
async def cmd_admin_panel(message: types.Message):
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

@dp.message_handler(lambda message: message.text == 'Управление наградами')
async def cmd_manage_rewards(message: types.Message):
    await message.answer(
        "🛠 Управление наградами:\n\n"
        "Выберите награду для редактирования:",
        reply_markup=get_manage_rewards_keyboard()
    )

# Обработка callback'ов для наград
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('reward_'))
async def process_reward_callback(callback_query: types.CallbackQuery):
    reward_id = int(callback_query.data.split('_')[1])
    reward = db_session.query(Reward).filter(Reward.id == reward_id).first()
    user_balance = get_user_balance(callback_query.from_user.id)
    
    if not reward:
        await callback_query.answer("Награда не найдена")
        return
    
    if not reward.file_id:
        await callback_query.answer("Файл для этой награды еще не загружен")
        return
    
    # Проверяем достаточно ли баллов
    if user_balance < reward.points_cost:
        await callback_query.answer(f"Недостаточно баллов! Нужно {reward.points_cost}, у вас {user_balance}")
        return
    
    try:
        # Списываем баллы
        if create_transaction(
            user_id=callback_query.from_user.id,
            reward_id=reward.id,
            points_change=-reward.points_cost,
            transaction_type="purchase"
        ):
            await bot.send_document(
                callback_query.from_user.id,
                reward.file_id,
                caption=f"🎉 Поздравляем! Вы получили: {reward.title}\n\n"
                       f"Списано баллов: {reward.points_cost}\n"
                       f"Остаток баллов: {get_user_balance(callback_query.from_user.id)}"
            )
            await callback_query.answer("Награда отправлена! Баллы списаны.")
        else:
            await callback_query.answer("Ошибка при списании баллов")
            
    except Exception as e:
        await callback_query.answer("Ошибка при отправке файла")
        logging.error(f"Error sending file: {e}")

@dp.callback_query_handler(lambda c: c.data == 'not_enough_points')
async def process_not_enough_points(callback_query: types.CallbackQuery):
    user_balance = get_user_balance(callback_query.from_user.id)
    await callback_query.answer(f"Недостаточно баллов! Ваш баланс: {user_balance}")

# Обработка управления наградами
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('view_reward_'))
async def process_view_reward(callback_query: types.CallbackQuery):
    reward_id = int(callback_query.data.split('_')[2])
    reward = db_session.query(Reward).filter(Reward.id == reward_id).first()
    
    if reward:
        status = "✅ Файл загружен" if reward.file_id else "❌ Файл отсутствует"
        # Считаем сколько раз награду покупали
        purchase_count = db_session.query(Transaction).filter(
            Transaction.reward_id == reward.id,
            Transaction.transaction_type == "purchase"
        ).count()
        
        text = (f"📊 Информация о награде:\n\n"
               f"Название: {reward.title}\n"
               f"Цена: {reward.points_cost} баллов\n"
               f"Статус: {status}\n"
               f"Куплена раз: {purchase_count}")
        await callback_query.message.answer(text)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('edit_reward_'))
async def process_edit_reward(callback_query: types.CallbackQuery):
    reward_id = int(callback_query.data.split('_')[2])
    reward = db_session.query(Reward).filter(Reward.id == reward_id).first()
    
    if reward:
        await callback_query.message.answer(
            f"Редактирование награды: {reward.title}\n\n"
            f"Текущая цена: {reward.points_cost} баллов\n\n"
            "Введите новую цену в баллах:"
        )
        await AdminStates.waiting_for_reward_edit_points.set()
        await dp.current_state().update_data(reward_id=reward_id)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('delete_reward_'))
async def process_delete_reward(callback_query: types.CallbackQuery):
    reward_id = int(callback_query.data.split('_')[2])
    reward = db_session.query(Reward).filter(Reward.id == reward_id).first()
    
    if reward:
        db_session.delete(reward)
        db_session.commit()
        await callback_query.message.answer(f"Награда '{reward.title}' удалена!")
    else:
        await callback_query.message.answer("Награда не найдена")
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'back_to_admin')
async def process_back_to_admin(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Админ панель:", reply_markup=get_admin_keyboard())
    await callback_query.answer()

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

@dp.message_handler(state=AdminStates.waiting_for_reward_edit_points)
async def process_edit_reward_points(message: types.Message, state: FSMContext):
    try:
        points = int(message.text)
        if points <= 0:
            await message.answer("Стоимость должна быть положительным числом. Попробуйте еще раз:")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите число. Попробуйте еще раз:")
        return
    
    async with state.proxy() as data:
        reward_id = data['reward_id']
        reward = db_session.query(Reward).filter(Reward.id == reward_id).first()
        
        if reward:
            old_points = reward.points_cost
            reward.points_cost = points
            db_session.commit()
            await message.answer(f"Цена награды '{reward.title}' изменена с {old_points} на {points} баллов!")
        else:
            await message.answer("Награда не найдена")
    
    await state.finish()

if __name__ == '__main__':
    # Инициализируем начальные награды
    initialize_rewards()
    
    # Запускаем бота
    logging.info("Bot starting...")
    executor.start_polling(dp, skip_updates=True)
