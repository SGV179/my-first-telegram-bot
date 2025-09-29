import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Database configuration
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '6432')
    
    # Admin configuration
    ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
    
    # Channels configuration
    CHANNEL_1 = os.getenv('CHANNEL_1')
    CHANNEL_2 = os.getenv('CHANNEL_2')
    CHANNEL_1_ID = int(os.getenv('CHANNEL_1_ID'))
    CHANNEL_2_ID = int(os.getenv('CHANNEL_2_ID'))
    
    # Database URL
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

config = Config()
