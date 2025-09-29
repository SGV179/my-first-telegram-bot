from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database.base import Base  # Изменено с connections на base

class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(20), default='user')
    registration_date = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    
    # Связи
    events = relationship("UserEvent", back_populates="user")
    scores = relationship("UserScore", back_populates="user")
    subscriptions = relationship("ChannelSubscription", back_populates="user")

class ChannelSubscription(Base):
    """Подписки пользователей на каналы"""
    __tablename__ = 'channel_subscriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    channel_id = Column(BigInteger, nullable=False)
    subscribed_at = Column(DateTime, default=datetime.now)
    is_subscribed = Column(Boolean, default=True)
    
    user = relationship("User")

class UserScore(Base):
    """Баллы пользователей"""
    __tablename__ = 'user_scores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    total_score = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.now)
    
    user = relationship("User")

class ScheduledPost(Base):
    """Отложенные посты"""
    __tablename__ = 'scheduled_posts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(BigInteger, nullable=False)
    post_text = Column(Text)
    scheduled_time = Column(DateTime, nullable=False)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class UserEvent(Base):
    """События пользователей для аналитики"""
    __tablename__ = 'user_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_type = Column(String(50), nullable=False)  # 'message', 'like', 'comment', 'subscribe'
    channel_id = Column(BigInteger)
    post_id = Column(BigInteger)
    event_data = Column(JSON)  # Гибкие данные события
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="events")

class DailyStat(Base):
    """Ежедневная статистика по каналам"""
    __tablename__ = 'daily_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    channel_id = Column(BigInteger, nullable=False)
    metrics = Column(JSON)  # {total_users: 100, new_users: 10, likes: 500}
    created_at = Column(DateTime, default=datetime.now)
