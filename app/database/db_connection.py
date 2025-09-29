import psycopg2
import logging
from app.config.config import config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                host=config.POSTGRES_HOST,
                database=config.POSTGRES_DB,
                user=config.POSTGRES_USER,
                password=config.POSTGRES_PASSWORD,
                port=config.POSTGRES_PORT,
                sslmode='require'
            )
            logger.info("✅ Successfully connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            raise

    def get_connection(self):
        if self.connection is None or self.connection.closed:
            self.connect()
        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

# Global database instance
db = Database()
