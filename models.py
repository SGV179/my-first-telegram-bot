#!/usr/bin/env python3
"""
Модели базы данных
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, ForeignKey, JSON, Text

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False, unique=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(20))
    registration_date = Column(DateTime)
    is_active = Column(Boolean)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class UserEvent(Base):
    __tablename__ = 'user_events'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_type = Column(String(50), nullable=False)
    channel_id = Column(BigInteger)
    post_id = Column(BigInteger)
    event_data = Column(JSON)
    created_at = Column(DateTime)
    
    def __repr__(self):
        return f"<UserEvent(id={self.id}, type='{self.event_type}')>"

class ChannelSubscription(Base):
    __tablename__ = 'channel_subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    channel_id = Column(BigInteger, nullable=False)
    subscribed_at = Column(DateTime)
    is_subscribed = Column(Boolean)

class UserScores(Base):
    __tablename__ = 'user_scores'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    total_score = Column(Integer)
    last_updated = Column(DateTime)

class ScheduledPosts(Base):
    __tablename__ = 'scheduled_posts'
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(BigInteger, nullable=False)
    post_text = Column(Text)
    scheduled_time = Column(DateTime, nullable=False)
    is_published = Column(Boolean)
    created_at = Column(DateTime)

class DailyStats(Base):
    __tablename__ = 'daily_stats'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    channel_id = Column(BigInteger, nullable=False)
    metrics = Column(JSON)
    created_at = Column(DateTime)
