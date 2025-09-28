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

# Команды администратора
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
            f"/loyalty - правила программы лояльности"
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
            f"/rewards - доступные награды\n\n"
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
    
    await callback.answer()

async def show_admin_main_menu(callback: types.CallbackQuery):
    """Показывает главное меню админ-панели"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📊 Статистика системы", callback_data="admin_stats")],
            [types.InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_users")],
            [types.InlineKeyboardButton(text="⚙️ Настройки баллов", callback_data="admin_scores")],
            [types.InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")]
        ]
    )
    
    await callback.message.edit_text(
        "🛠️ Панель администратора\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

async def show_system_stats(callback: types.CallbackQuery):
    """Показывает статистику системы"""
    from database.connections import get_db
    from database.models import User, ChannelSubscription, UserEvent, UserScore
    
    db = next(get_db())
    
    total_users = db.query(User).count()
    active_subs = db.query(ChannelSubscription).filter(ChannelSubscription.is_subscribed == True).count()
    total_events = db.query(UserEvent).count()
    total_scores = db.query(UserScore).filter(UserScore.total_score > 0).count()
    
    # Статистика по каналам
    channel_stats = []
    for name, channel_id in settings.CHANNELS.items():
        subs = db.query(ChannelSubscription).filter(
            ChannelSubscription.channel_id == channel_id,
            ChannelSubscription.is_subscribed == True
        ).count()
        channel_stats.append(f"• {name}: {subs} подписчиков")
    
    message = (
        "📊 Статистика системы:\n\n"
        f"👤 Всего пользователей: {total_users}\n"
        f"✅ Активных подписок: {active_subs}\n"
        f"🎯 Всего событий: {total_events}\n"
        f"⭐ Пользователей с баллами: {total_scores}\n\n"
        "📺 Подписчики по каналам:\n" + "\n".join(channel_stats)
    )
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")],
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
        ]
    )
    
    await callback.message.edit_text(message, reply_markup=keyboard)

async def show_user_management(callback: types.CallbackQuery):
    """Показывает управление пользователями"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_user_list")],
            [types.InlineKeyboardButton(text="🔍 Поиск пользователя", callback_data="admin_user_search")],
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
        ]
    )
    
    await callback.message.edit_text(
        "👥 Управление пользователями\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

async def show_user_list(callback: types.CallbackQuery):
    """Показывает список пользователей"""
    from database.connections import get_db
    from database.models import User
    
    db = next(get_db())
    users = db.query(User).order_by(User.registration_date.desc()).limit(10).all()
    
    if not users:
        message = "👥 Пользователи не найдены"
    else:
        message = "👥 Последние 10 пользователей:\n\n"
        for i, user in enumerate(users, 1):
            message += f"{i}. {user.first_name or 'No name'} (@{user.username or 'no_username'})\n"
            message += f"   ID: {user.telegram_id}, Зарегистрирован: {user.registration_date.strftime('%d.%m.%Y')}\n\n"
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_users")],
            [types.InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_user_list")]
        ]
    )
    
    await callback.message.edit_text(message, reply_markup=keyboard)

async def show_user_search(callback: types.CallbackQuery):
    """Показывает меню поиска пользователя"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_users")]
        ]
    )
    
    await callback.message.edit_text(
        "🔍 Поиск пользователя\n\n"
        "Для поиска пользователя отправьте его Telegram ID или username в формате:\n"
        "<code>/find 123456789</code> - поиск по ID\n"
        "<code>/find @username</code> - поиск по username",
        reply_markup=keyboard
    )

async def show_score_settings(callback: types.CallbackQuery):
    """Показывает настройки баллов"""
    message = (
        "⚙️ Настройки системы баллов\n\n"
        "Текущие настройки:\n"
        f"🎁 Приветственные: {settings.SCORING['welcome']} баллов\n"
        f"💬 Комментарии: {settings.SCORING['comment']} баллов\n"
        f"🔄 Репосты: {settings.SCORING['repost']} баллов\n"
        f"👍 Лайки: {settings.SCORING['like']} балл\n"
        f"👎 Дизлайки: {settings.SCORING['dislike']} баллов\n"
        f"🔘 Кнопки: {settings.SCORING['button_click']} баллов\n"
        f"👥 Рефералы: {settings.SCORING['referral']} баллов\n\n"
        "Для изменения настроек обратитесь к разработчику."
    )
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
        ]
    )
    
    await callback.message.edit_text(message, reply_markup=keyboard)

async def show_broadcast_menu(callback: types.CallbackQuery):
    """Показывает меню рассылки"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📢 Создать рассылку", callback_data="admin_broadcast_create")],
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
        ]
    )
    
    await callback.message.edit_text(
        "📢 Рассылка сообщений\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

async def show_broadcast_create(callback: types.CallbackQuery):
    """Показывает создание рассылки"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_broadcast")]
        ]
    )
    
    await callback.message.edit_text(
        "📢 Создание рассылки\n\n"
        "Для создания рассылки отправьте сообщение в формате:\n"
        "<code>/broadcast Ваш текст рассылки</code>\n\n"
        "Сообщение будет отправлено всем пользователям бота.",
        reply_markup=keyboard
    )

# Главная функция для запуска бота
async def main():
    create_tables()
    logger.info("✅ База данных инициализирована")
    logger.info(f"🚀 Бот запускается... Администраторы: {settings.ADMINS}")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
