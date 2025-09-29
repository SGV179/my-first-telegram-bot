from config.settings import settings

LOYALTY_PROGRAM_RULES = {
    "title": "🎁 Программа лояльности Golden Channels",
    "description": (
        "Накопительная система баллов для активных подписчиков каналов "
        "@golden_square_1 и @golden_asset_1"
    ),
    "requirements": [
        "✅ Быть подписанным на бота @tg_admin_channel_bot",
        "✅ Быть подписанным на оба канала: @golden_square_1 и @golden_asset_1",
        "✅ Активно участвовать в жизни каналов"
    ],
    "scoring_rules": [
        f"🎁 Приветственные баллы: {settings.SCORING['welcome']} баллов за подписку на бота и оба канала",
        f"💬 Комментарии: {settings.SCORING['comment']} баллов за каждый комментарий под постом или комментарием",
        f"🔄 Репосты: {settings.SCORING['repost']} балла за каждый репост поста",
        f"👍 Лайки: {settings.SCORING['like']} балл за каждый лайк поста или комментария",
        f"👎 Дизлайки: баллы не начисляются",
        f"🔘 Кнопки: {settings.SCORING['button_click']} баллов за нажатие кнопки под постом",
        f"👥 Приглашения: {settings.SCORING['referral']} баллов за каждого приглашенного пользователя"
    ],
    "important_notes": [
        "⚠️ Баллы начисляются только при активной подписке на бота и оба канала",
        "⚠️ При отписке от бота или любого из каналов все баллы обнуляются",
        "⚠️ При отмене действия (удаление комментария, снятие лайка) баллы вычитаются",
        "🔄 Баллы можно обменивать на информационные материалы и подарки"
    ],
    "rewards": [
        "📚 Эксклюзивные образовательные материалы",
        "🎁 Подарки и сувениры от администрации",
        "💼 Полезные шаблоны и инструменты",
        "👑 Специальные статусы в сообществе"
    ]
}

def get_loyalty_rules_message():
    """Возвращает форматированное сообщение с правилами программы лояльности"""
    rules = LOYALTY_PROGRAM_RULES
    
    message = f"<b>{rules['title']}</b>\n\n"
    message += f"{rules['description']}\n\n"
    
    message += "<b>📋 Условия участия:</b>\n"
    for requirement in rules['requirements']:
        message += f"{requirement}\n"
    
    message += "\n<b>💰 Начисление баллов:</b>\n"
    for rule in rules['scoring_rules']:
        message += f"• {rule}\n"
    
    message += "\n<b>⚠️ Важные примечания:</b>\n"
    for note in rules['important_notes']:
        message += f"• {note}\n"
    
    message += "\n<b>🎁 Доступные награды:</b>\n"
    for reward in rules['rewards']:
        message += f"• {reward}\n"
    
    message += "\n📊 Для просмотра своих баллов используйте команду /stats"
    
    return message
