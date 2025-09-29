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
from datetime import datetime, timedelta

from models import Base, Reward, User, Transaction, Activity, UserActivity

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
    waiting_for_activity_title = State()
    waiting_for_activity_points = State()
    waiting_for_activity_cooldown = State()

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

def create_transaction(user_id, reward_id, points_change, transaction_type, description=None):
    """Создает запись о транзакции"""
    user = db_session.query(User).filter(User.user_id == user_id).first()
    if user:
        transaction = Transaction(
            user_id=user.id,
            reward_id=reward_id,
            points_change=points_change,
            transaction_type=transaction_type,
            description=description
        )
        db_session.add(transaction)
        
        # Обновляем баланс пользователя
        user.points += points_change
        db_session.commit()
        return True
    return False

def can_complete_activity(user_id, activity_id):
    """Проверяет, может ли пользователь выполнить активность"""
    user = db_session.query(User).filter(User.user_id == user_id).first()
    activity = db_session.query(Activity).filter(Activity.id == activity_id).first()
    
    if not user or not activity or not activity.is_active:
        return False, "Активность недоступна"
    
    # Проверяем максимальное количество выполнений
    if activity.max_completions > 0:
        completions_count = db_session.query(UserActivity).filter(
            UserActivity.user_id == user.id,
            UserActivity.activity_id == activity.id
        ).count()
        
        if completions_count >= activity.max_completions:
            return False, f"Достигнут лимит выполнений ({activity.max_completions})"
    
    # Проверяем кулдаун
    if activity.cooldown_hours > 0:
        last_completion = db_session.query(UserActivity).filter(
            UserActivity.user_id == user.id,
            UserActivity.activity_id == activity.id
        ).order_by(UserActivity.completed_at.desc()).first()
        
        if last_completion:
            cooldown_end = last_completion.completed_at + timedelta(hours=activity.cooldown_hours)
            if datetime.now() < cooldown_end:
                time_left = cooldown_end - datetime.now()
                hours_left = int(time_left.total_seconds() // 3600)
                minutes_left = int((time_left.total_seconds() % 3600) // 60)
                return False, f"Доступно через {hours_left}ч {minutes_left}м"
    
    return True, "Можно выполнить"

# Клавиатуры
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Мой профиль'))
    keyboard.add(KeyboardButton('Каталог наград'))
    keyboard.add(KeyboardButton('Заработать баллы'))
    keyboard.add(KeyboardButton('Админ панель'))
    return keyboard

def get_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Добавить награду'))
    keyboard.add(KeyboardButton('Список наград'))
    keyboard.add(KeyboardButton('Управление наградами'))
    keyboard.add(KeyboardButton('Управление активностями'))
    keyboard.add(KeyboardButton('На главную'))
    return keyboard

def get_activities_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Ежедневные активности'))
    keyboard.add(KeyboardButton('Разовые задания'))
    keyboard.add(KeyboardButton('На главную'))
    return keyboard

def get_rewards_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    rewards = db_session.query(Reward).all()
    user_balance = get_user_balance(user_id)
    
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

def get_activities_list_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    activities = db_session.query(Activity).filter(Activity.is_active == True).all()
    
    for activity in activities:
        can_complete, message = can_complete_activity(user_id, activity.id)
        status_icon = "✅" if can_complete else "⏳"
        
        button_text = f"{status_icon} {activity.title} - {activity.points_reward} баллов"
        if len(button_text) > 50:
            button_text = f"{status_icon} {activity.title[:47]}..."
        
        callback_data = f"complete_activity_{activity.id}" if can_complete else f"activity_info_{activity.id}"
        
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

def get_manage_activities_keyboard():
    keyboard = InlineKeyboardMarkup()
    activities = db_session.query(Activity).all()
    
    for activity in activities:
        status = "✅" if activity.is_active else "❌"
        button_text = f"{status} {activity.title}"
        if len(button_text) > 30:
            button_text = f"{status} {activity.title[:27]}..."
        
        keyboard.row(
            InlineKeyboardButton(
                button_text,
                callback_data=f"view_activity_{activity.id}"
            ),
            InlineKeyboardButton(
                "✏️",
                callback_data=f"edit_activity_{activity.id}"
            ),
            InlineKeyboardButton(
                "❌", 
                callback_data=f"delete_activity_{activity.id}"
            )
        )
    
    keyboard.add(InlineKeyboardButton("Добавить активность", callback_data="add_activity"))
    keyboard.add(InlineKeyboardButton("Назад в админку", callback_data="back_to_admin"))
    return keyboard

# Инициализация активностей
def initialize_activities():
    """Создает начальные активности, если их нет"""
    existing_activities = db_session.query(Activity).count()
    if existing_activities == 0:
        initial_activities = [
            {
                "title": "Ежедневный вход",
                "description": "Зайдите в бота сегодня",
                "points_reward": 5,
                "cooldown_hours": 24,
                "max_completions": 0
            },
            {
                "title": "Просмотр каталога наград",
                "description": "Откройте раздел с наградами",
                "points_reward": 3,
                "cooldown_hours": 6,
                "max_completions": 0
            },
            {
                "title": "Первый визит",
                "description": "Впервые зашли в бота",
                "points_reward": 10,
                "cooldown_hours": 0,
                "max_completions": 1
            },
            {
                "title": "Изучение профиля",
                "description": "Посмотрите свой профиль",
                "points_reward": 2,
                "cooldown_hours": 12,
                "max_completions": 0
            }
        ]
        
        for activity_data in initial_activities:
            activity = Activity(
                title=activity_data["title"],
                description=activity_data["description"],
                points_reward=activity_data["points_reward"],
                cooldown_hours=activity_data["cooldown_hours"],
                max_completions=activity_data["max_completions"]
            )
            db_session.add(activity)
        
        db_session.commit()
        logging.info("Initial activities added to database")

# Очистка базы от дубликатов
def cleanup_duplicates():
    """Удаляет дубликаты наград по названию"""
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
    user = get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Автоматически начисляем баллы за первый визит
    first_visit_activity = db_session.query(Activity).filter(Activity.title == "Первый визит").first()
    if first_visit_activity:
        can_complete, _ = can_complete_activity(message.from_user.id, first_visit_activity.id)
        if can_complete:
            user_activity = UserActivity(
                user_id=user.id,
                activity_id=first_visit_activity.id
            )
            db_session.add(user_activity)
            create_transaction(
                user_id=message.from_user.id,
                reward_id=None,
                points_change=first_visit_activity.points_reward,
                transaction_type="activity",
                description=f"Начисление за: {first_visit_activity.title}"
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
    
    # Начисляем баллы за просмотр профиля
    profile_activity = db_session.query(Activity).filter(Activity.title == "Изучение профиля").first()
    if profile_activity:
        can_complete, _ = can_complete_activity(message.from_user.id, profile_activity.id)
        if can_complete:
            user_activity = UserActivity(
                user_id=user.id,
                activity_id=profile_activity.id
            )
            db_session.add(user_activity)
            create_transaction(
                user_id=message.from_user.id,
                reward_id=None,
                points_change=profile_activity.points_reward,
                transaction_type="activity",
                description=f"Начисление за: {profile_activity.title}"
            )
            profile_bonus = f"\n🎉 +{profile_activity.points_reward} баллов за изучение профиля!"
        else:
            profile_bonus = ""
    else:
        profile_bonus = ""
    
    # Получаем историю последних операций
    recent_transactions = db_session.query(Transaction).filter(
        Transaction.user_id == user.id
    ).order_by(Transaction.created_at.desc()).limit(5).all()
    
    transactions_text = "\n📊 Последние операции:\n"
    for transaction in recent_transactions:
        sign = "+" if transaction.points_change > 0 else ""
        transactions_text += f"  {sign}{transaction.points_change} баллов - {transaction.description or transaction.transaction_type}\n"
    
    await message.answer(
        f"👤 Ваш профиль:\n\n"
        f"Имя: {message.from_user.first_name or 'Не указано'}\n"
        f"Username: @{message.from_user.username or 'Не указан'}\n"
        f"Баланс: {user.points} баллов{profile_bonus}\n"
        f"{transactions_text}\n"
        f"Используйте баллы для получения полезных материалов!"
    )

@dp.message_handler(lambda message: message.text == 'Каталог наград')
async def cmd_rewards_catalog(message: types.Message):
    # Начисляем баллы за просмотр каталога
    catalog_activity = db_session.query(Activity).filter(Activity.title == "Просмотр каталога наград").first()
    if catalog_activity:
        can_complete, _ = can_complete_activity(message.from_user.id, catalog_activity.id)
        if can_complete:
            user = get_or_create_user(message.from_user.id)
            user_activity = UserActivity(
                user_id=user.id,
                activity_id=catalog_activity.id
            )
            db_session.add(user_activity)
            create_transaction(
                user_id=message.from_user.id,
                reward_id=None,
                points_change=catalog_activity.points_reward,
                transaction_type="activity",
                description=f"Начисление за: {catalog_activity.title}"
            )
    
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

@dp.message_handler(lambda message: message.text == 'Заработать баллы')
async def cmd_earn_points(message: types.Message):
    user_balance = get_user_balance(message.from_user.id)
    
    text = (
        f"💎 Заработать баллы\n\n"
        f"Ваш текущий баланс: {user_balance} баллов\n\n"
        f"Выполняйте активности и задания, чтобы получать баллы!\n\n"
        f"Выберите тип активностей:"
    )
    
    await message.answer(text, reply_markup=get_activities_keyboard())

@dp.message_handler(lambda message: message.text == 'Ежедневные активности')
async def cmd_daily_activities(message: types.Message):
    activities = db_session.query(Activity).filter(
        Activity.is_active == True,
        Activity.cooldown_hours > 0
    ).all()
    
    if not activities:
        await message.answer("Пока нет ежедневных активностей.")
        return
    
    text = "📅 Ежедневные активности:\n\n"
    for activity in activities:
        can_complete, message_text = can_complete_activity(message.from_user.id, activity.id)
        status = "✅ Доступно" if can_complete else f"⏳ {message_text}"
        text += f"• {activity.title}\n  Награда: {activity.points_reward} баллов\n  {status}\n\n"
    
    text += "Выберите активность для выполнения:"
    await message.answer(text, reply_markup=get_activities_list_keyboard(message.from_user.id))

@dp.message_handler(lambda message: message.text == 'Разовые задания')
async def cmd_one_time_activities(message: types.Message):
    activities = db_session.query(Activity).filter(
        Activity.is_active == True,
        Activity.max_completions > 0
    ).all()
    
    if not activities:
        await message.answer("Пока нет разовых заданий.")
        return
    
    text = "🎯 Разовые задания:\n\n"
    for activity in activities:
        can_complete, message_text = can_complete_activity(message.from_user.id, activity.id)
        user = get_or_create_user(message.from_user.id)
        completions_count = db_session.query(UserActivity).filter(
            UserActivity.user_id == user.id,
            UserActivity.activity_id == activity.id
        ).count()
        
        status = "✅ Доступно" if can_complete else f"❌ {message_text}"
        progress = f" ({completions_count}/{activity.max_completions})"
        
        text += f"• {activity.title}{progress}\n  Награда: {activity.points_reward} баллов\n  {status}\n\n"
    
    text += "Выберите задание для выполнения:"
    await message.answer(text, reply_markup=get_activities_list_keyboard(message.from_user.id))

@dp.message_handler(lambda message: message.text == 'Админ панель')
async def cmd_admin_panel(message: types.Message):
    await message.answer(
        "👨‍💻 Админ панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )

# Админские команды
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

@dp.message_handler(lambda message: message.text == 'Управление активностями')
async def cmd_manage_activities(message: types.Message):
    await message.answer(
        "🎯 Управление активностями:\n\n"
        "Выберите активность для редактирования:",
        reply_markup=get_manage_activities_keyboard()
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
    
    if user_balance < reward.points_cost:
        await callback_query.answer(f"Недостаточно баллов! Нужно {reward.points_cost}, у вас {user_balance}")
        return
    
    try:
        if create_transaction(
            user_id=callback_query.from_user.id,
            reward_id=reward.id,
            points_change=-reward.points_cost,
            transaction_type="purchase",
            description=f"Покупка: {reward.title}"
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

# Обработка callback'ов для активностей
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('complete_activity_'))
async def process_complete_activity(callback_query: types.CallbackQuery):
    activity_id = int(callback_query.data.split('_')[2])
    activity = db_session.query(Activity).filter(Activity.id == activity_id).first()
    user = get_or_create_user(callback_query.from_user.id)
    
    if not activity:
        await callback_query.answer("Активность не найдена")
        return
    
    can_complete, message = can_complete_activity(callback_query.from_user.id, activity_id)
    
    if can_complete:
        # Записываем выполнение активности
        user_activity = UserActivity(
            user_id=user.id,
            activity_id=activity.id
        )
        db_session.add(user_activity)
        
        # Начисляем баллы
        create_transaction(
            user_id=callback_query.from_user.id,
            reward_id=None,
            points_change=activity.points_reward,
            transaction_type="activity",
            description=f"Начисление за: {activity.title}"
        )
        
        await callback_query.answer(f"🎉 +{activity.points_reward} баллов за выполнение задания!")
        await callback_query.message.answer(
            f"✅ Задание выполнено!\n\n"
            f"Активность: {activity.title}\n"
            f"Начислено: {activity.points_reward} баллов\n"
            f"Новый баланс: {get_user_balance(callback_query.from_user.id)} баллов"
        )
    else:
        await callback_query.answer(message)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('activity_info_'))
async def process_activity_info(callback_query: types.CallbackQuery):
    activity_id = int(callback_query.data.split('_')[2])
    activity = db_session.query(Activity).filter(Activity.id == activity_id).first()
    
    if activity:
        can_complete, message = can_complete_activity(callback_query.from_user.id, activity_id)
        
        text = (
            f"📋 Информация об активности:\n\n"
            f"Название: {activity.title}\n"
            f"Описание: {activity.description}\n"
            f"Награда: {activity.points_reward} баллов\n"
            f"Статус: {message}\n"
        )
        
        if activity.cooldown_hours > 0:
            text += f"Кулдаун: {activity.cooldown_hours} часов\n"
        
        if activity.max_completions > 0:
            user = get_or_create_user(callback_query.from_user.id)
            completions_count = db_session.query(UserActivity).filter(
                UserActivity.user_id == user.id,
                UserActivity.activity_id == activity.id
            ).count()
            text += f"Выполнено: {completions_count}/{activity.max_completions}"
        
        await callback_query.message.answer(text)
    
    await callback_query.answer()

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

# Обработка управления активностями
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('view_activity_'))
async def process_view_activity(callback_query: types.CallbackQuery):
    activity_id = int(callback_query.data.split('_')[2])
    activity = db_session.query(Activity).filter(Activity.id == activity_id).first()
    
    if activity:
        completions_count = db_session.query(UserActivity).filter(
            UserActivity.activity_id == activity.id
        ).count()
        
        text = (f"📊 Информация об активности:\n\n"
               f"Название: {activity.title}\n"
               f"Описание: {activity.description}\n"
               f"Награда: {activity.points_reward} баллов\n"
               f"Кулдаун: {activity.cooldown_hours} часов\n"
               f"Макс. выполнений: {activity.max_completions if activity.max_completions > 0 else 'Без ограничений'}\n"
               f"Статус: {'✅ Активна' if activity.is_active else '❌ Неактивна'}\n"
               f"Выполнено раз: {completions_count}")
        await callback_query.message.answer(text)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'add_activity')
async def process_add_activity(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Введите название новой активности:")
    await AdminStates.waiting_for_activity_title.set()
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

# Обработка добавления активностей
@dp.message_handler(state=AdminStates.waiting_for_activity_title)
async def process_activity_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = message.text
    
    await message.answer("Введите описание активности:")
    await AdminStates.waiting_for_activity_points.set()

@dp.message_handler(state=AdminStates.waiting_for_activity_points)
async def process_activity_points(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text
    
    await message.answer("Введите количество баллов за выполнение:")
    await AdminStates.waiting_for_activity_cooldown.set()

@dp.message_handler(state=AdminStates.waiting_for_activity_cooldown)
async def process_activity_cooldown(message: types.Message, state: FSMContext):
    try:
        points = int(message.text)
        if points <= 0:
            await message.answer("Количество баллов должно быть положительным числом. Попробуйте еще раз:")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите число. Попробуйте еще раз:")
        return
    
    async with state.proxy() as data:
        data['points_reward'] = points
    
    await message.answer(
        "Введите время ожидания между выполнениями (в часах):\n"
        "0 - без ограничений\n"
        "24 - раз в сутки\n"
        "168 - раз в неделю"
    )
    
    # Сохраняем данные и переходим к следующему шагу
    await state.update_data(points_reward=points)

@dp.message_handler(state=AdminStates.waiting_for_activity_cooldown)
async def process_activity_final(message: types.Message, state: FSMContext):
    try:
        cooldown = int(message.text)
        if cooldown < 0:
            await message.answer("Время ожидания не может быть отрицательным. Попробуйте еще раз:")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите число. Попробуйте еще раз:")
        return
    
    async with state.proxy() as data:
        activity = Activity(
            title=data['title'],
            description=data['description'],
            points_reward=data['points_reward'],
            cooldown_hours=cooldown,
            max_completions=0  # По умолчанию без ограничений
        )
        
        db_session.add(activity)
        db_session.commit()
    
    await message.answer(
        f"Активность '{data['title']}' успешно добавлена!\n\n"
        f"Награда: {data['points_reward']} баллов\n"
        f"Кулдаун: {cooldown} часов"
    )
    await state.finish()

if __name__ == '__main__':
    # Инициализируем начальные награды и активности
    initialize_rewards()
    initialize_activities()
    
    # Запускаем бота
    logging.info("Bot starting...")
    executor.start_polling(dp, skip_updates=True)
