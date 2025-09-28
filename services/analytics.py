#!/usr/bin/env python3
"""
Сервис аналитики для работы с базой данных
"""

from sqlalchemy.orm import Session

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user(self, telegram_id, username=None, first_name=None, last_name=None):
        """Создает или возвращает существующего пользователя"""
        from models import User
        from datetime import datetime
        
        user = self.db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                registration_date=datetime.now(),
                is_active=True
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            print(f"✅ Создан новый пользователь: {username} (ID: {user.id})")
        else:
            print(f"✅ Найден существующий пользователь: {user.username} (ID: {user.id})")
        
        return user

    def track_event(self, user_id, event_type, channel_id=None, post_id=None, event_data=None):
        """Записывает событие пользователя"""
        from models import UserEvent
        from datetime import datetime
        import json
        
        event = UserEvent(
            user_id=user_id,
            event_type=event_type,
            channel_id=channel_id,
            post_id=post_id,
            event_data=json.dumps(event_data) if event_data else None,
            created_at=datetime.now()
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_daily_stats(self, channel_id):
        """Возвращает статистику за день"""
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        # Простой пример - можно расширить
        stats = {
            "date": today,
            "channel_id": channel_id,
            "total_events": 0,
            "unique_users": 0
        }
        
        return stats
