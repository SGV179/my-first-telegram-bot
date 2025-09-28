from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    points = Column(Integer, default=100)  # Начальный баланс 100 баллов
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Связь с историей операций
    transactions = relationship("Transaction", back_populates="user")
    
    def __repr__(self):
        return f"User(id={self.id}, user_id={self.user_id}, points={self.points})"

class Reward(Base):
    __tablename__ = 'rewards'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_id = Column(String(255))  # ID файла в Telegram
    file_name = Column(String(255))
    points_cost = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Связь с историей операций
    transactions = relationship("Transaction", back_populates="reward")
    
    def __repr__(self):
        return f"Reward(id={self.id}, title='{self.title}', points_cost={self.points_cost})"

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    reward_id = Column(Integer, ForeignKey('rewards.id'))
    points_change = Column(Integer, nullable=False)  # Отрицательное для списания
    transaction_type = Column(String(50), nullable=False)  # 'purchase', 'reward', etc.
    created_at = Column(DateTime, default=datetime.now)
    
    # Связи
    user = relationship("User", back_populates="transactions")
    reward = relationship("Reward", back_populates="transactions")
    
    def __repr__(self):
        return f"Transaction(id={self.id}, user_id={self.user_id}, points_change={self.points_change})"
