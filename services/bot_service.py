#!/usr/bin/env python3
"""
Сервис для интеграции базы данных с ботом
"""

from services.analytics import AnalyticsService
from config.database import get_db_session

class BotService:
    def __init__(self):
        self.db = get_db_session()
        self.analytics = AnalyticsService(self.db)
    
    def register_user(self, telegram_id, username, first_name, last_name):
        """Регистрирует пользователя в базе данных"""
        user = self.analytics.get_or_create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        return user
    
    def track_user_event(self, user_id, event_type, **kwargs):
        """Отслеживает событие пользователя"""
        event = self.analytics.track_event(
            user_id=user_id,
            event_type=event_type,
            **kwargs
        )
        return event
    
    def get_user_stats(self, user_id):
        """Возвращает статистику пользователя"""
        # Здесь можно добавить логику для получения статистики пользователя
        return {"user_id": user_id, "events_count": 0}
    
    def close_connection(self):
        """Закрывает соединение с базой данных"""
        self.db.close()
