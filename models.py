from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Reward(Base):
    __tablename__ = 'rewards'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_id = Column(String(255))  # ID файла в Telegram
    file_name = Column(String(255))
    points_cost = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"Reward(id={self.id}, title='{self.title}', points_cost={self.points_cost})"

