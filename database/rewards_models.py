from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.base import Base  # Изменено с connections на base

class Reward(Base):
    """Модель награды за баллы"""
    __tablename__ = 'rewards'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    cost = Column(Integer, nullable=False)  # Стоимость в баллах
    category = Column(String(50), default='other')  # material, digital, status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Связи
    redemptions = relationship("RewardRedemption", back_populates="reward")

class RewardRedemption(Base):
    """Модель обмена баллов на награды"""
    __tablename__ = 'reward_redemptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reward_id = Column(Integer, ForeignKey('rewards.id'), nullable=False)
    redeemed_at = Column(DateTime, default=datetime.now)
    status = Column(String(20), default='pending')  # pending, completed, cancelled
    
    # Связи
    user = relationship("User")
    reward = relationship("Reward", back_populates="redemptions")
