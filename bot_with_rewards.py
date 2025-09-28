import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, ChatMemberUpdatedFilter
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database.connections import create_tables
from bots.handlers.channel_handlers_fixed import handle_chat_member_update
from bots.handlers.user_commands import cmd_stats, cmd_channels
from bots.handlers.bot_subscription_handler import handle_bot_subscription
from bots.handlers.loyalty_commands import cmd_loyalty, cmd_rewards
from bots.handlers.rewards_commands import cmd_shop, cmd_balance, handle_rewards_callback
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

# Проверка является ли пользователь администратором
def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMINS

# Регистрируем обработчики
dp.chat_member.register(handle_chat_member_update)  # Подписки на каналы
dp.chat_member.register(handle_bot_subscription)    # Подписка на самого бота
dp.message.register(cmd_stats, Command("stats"))
dp.message.register(cmd_channels, Command("channels"))
dp.message.register(cmd_loyalty, Command("loyalty"))
dp.message.register(cmd_rewards, Command("rewards"))
dp.message.register(cmd_shop, Command("shop"))
dp.message.register(cmd_balance, Command("balance"))

# Регистрируем callback-обработчики для наград
dp.callback_query.register(handle_rewards_callback, F.data.startswith(("buy_reward_", "my_balance", "redemption_history", "back_to_shop")))

# Команды администратора (остальной код из bot_admin_fixed.py остается без изменений)
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Панель администратора"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав доступа к панели администратора")
        return
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📊 Статистика системы", callback_data="admin_stats")],
            [types.InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_users")],
            [types.InlineKeyboardButton(text="⚙️ Настройки баллов", callback_data="admin_scores")],
            [types.InlineKeyboardButton(text="🎁 Управление наградами", callback_data="admin_rewards")],
            [types.InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")]
        ]
    )
    
    await message.answer(
        "🛠️ Панель администратора\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    
    if is_admin(user.id):
        # Специальное приветствие для администратора
        await message.answer(
            f"👋 Привет, администратор {user.first_name}!\n\n"
            f"Используй /admin для доступа к панели управления\n"
            f"/stats - статистика пользователя\n"
            f"/channels - список каналов\n"
            f"/loyalty - правила программы лояльности\n"
            f"/shop - магазин наград"
        )
    else:
        # Обычное приветствие для пользователей
        await message.answer(
            f"👋 Привет, {user.first_name}!\n\n"
            f"Я бот для администрирования каналов:\n"
            f"• @golden_square_1\n"
            f"• @golden_asset_1\n\n"
            f"📊 Используй команды:\n"
            f"/stats - твоя статистика\n"
            f"/channels - список каналов\n"
            f"/loyalty - программа лояльности\n"
            f"/rewards - доступные награды\n"
            f"/shop - магазин наград\n"
            f"/balance - твой баланс\n\n"
            f"Я отслеживаю активность в каналах и начисляю баллы! 🎁"
        )
    logger.info(f"Пользователь {user.id} запустил бота")

# Обработчик callback-запросов от админ-панели
@dp.callback_query(F.data.startswith("admin_"))
async def handle_admin_callback(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    action = callback.data
    
    if action == "admin_stats":
        await show_system_stats(callback)
    elif action == "admin_users":
        await show_user_management(callback)
    elif action == "admin_scores":
        await show_score_settings(callback)
    elif action == "admin_rewards":
        await show_rewards_management(callback)
    elif action == "admin_broadcast":
        await show_broadcast_menu(callback)
    elif action == "admin_back":
        await show_admin_main_menu(callback)
    elif action == "admin_user_list":
        await show_user_list(callback)
    elif action == "admin_user_search":
        await show_user_search(callback)
    elif action == "admin_broadcast_create":
        await show_broadcast_create(callback)
    elif action == "admin_rewards_list":
        await show_rewards_list(callback)
    elif action == "admin_rewards_add":
        await show_add_reward(callback)
    
    await callback.answer()

# Добавляем функцию управления наградами в админ-панели
async def show_rewards_management(callback: types.CallbackQuery):
    """Показывает управление наградами"""
    from services.rewards_service import RewardsService
    
    rewards_service = RewardsService()
    rewards_count = len(rewards_service.get_available_rewards())
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🎁 Список наград", callback_data="admin_rewards_list")],
            [types.InlineKeyboardButton(text="➕ Добавить награду", callback_data="admin_rewards_add")],
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
        ]
    )
    
    await callback.message.edit_text(
        f"🎁 Управление наградами\n\n"
        f"📊 Активных наград: {rewards_count}\n\n"
        f"Выберите действие:",
        reply_markup=keyboard
    )

async def show_rewards_list(callback: types.CallbackQuery):
    """Показывает список наград"""
    from services.rewards_service import RewardsService
    
    rewards_service = RewardsService()
    rewards = rewards_service.get_available_rewards()
    
    if not rewards:
        message = "🎁 Награды не найдены"
    else:
        message = "🎁 Список активных наград:\n\n"
        for i, reward in enumerate(rewards, 1):
            message += f"{i}. <b>{reward.name}</b>\n"
            message += f"   📝 {reward.description}\n"
            message += f"   💰 {reward.cost} баллов\n"
            message += f"   📂 Категория: {reward.category}\n\n"
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_rewards_list")],
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_rewards")]
        ]
    )
    
    await callback.message.edit_text(message, reply_markup=keyboard)

async def show_add_reward(callback: types.CallbackQuery):
    """Показывает добавление награды"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_rewards")]
        ]
    )
    
    await callback.message.edit_text(
        "➕ Добавление награды\n\n"
        "Для добавления награды используйте команду:\n"
        "<code>/add_reward Название|Описание|Стоимость|Категория</code>\n\n"
        "Пример:\n"
        "<code>/add_reward Электронная книга|Полезные материалы по инвестициям|50|digital</code>\n\n"
        "Категории: digital, material, status",
        reply_markup=keyboard
    )

# Остальные функции из bot_admin_fixed.py (show_system_stats, show_user_management, и т.д.)
# ... [вставьте сюда все остальные функции из bot_admin_fixed.py] ...

# Главная функция для запуска бота
async def main():
    create_tables()
    logger.info("✅ База данных инициализирована")
    logger.info(f"🚀 Бот запускается... Администраторы: {settings.ADMINS}")
    
    # Создаем начальные награды
    await create_initial_rewards()
    
    await dp.start_polling(bot)

async def create_initial_rewards():
    """Создает начальные награды в базе данных"""
    try:
        from database.connections import get_db
        from database.rewards_models import Reward
        
        db = next(get_db())
        
        # Проверяем, есть ли уже награды
        existing_rewards = db.query(Reward).count()
        if existing_rewards > 0:
            logger.info(f"✅ В базе уже есть {existing_rewards} наград")
            return
        
        # Создаем начальные награды
        initial_rewards = [
            {
                "name": "📚 Электронная книга",
                "description": "Эксклюзивные материалы по инвестициям и финансам",
                "cost": 50,
                "category": "digital"
            },
            {
                "name": "💼 Шаблон Excel",
                "description": "Полезные шаблоны для учета финансов и инвестиций",
                "cost": 30,
                "category
