from clickhouse_driver import Client
from database.cloud_config import CLICKHOUSE_CONFIG
import logging

logger = logging.getLogger(__name__)

class ClickHouseClient:
    def __init__(self):
        self.config = CLICKHOUSE_CONFIG
        self.client = None
        self._connect()
        
    def _connect(self):
        """Устанавливаем подключение к ClickHouse через HTTPS"""
        try:
            self.client = Client(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                secure=self.config['secure'],
                verify=False  # Отключаем проверку SSL сертификата
            )
            
            # Тестовый запрос
            result = self.client.execute('SELECT 1')
            logger.info("✅ HTTPS подключение к ClickHouse установлено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка HTTPS подключения: {e}")
            raise
    
    def execute(self, query, params=None):
        """Выполняет запрос к ClickHouse"""
        try:
            return self.client.execute(query, params)
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            raise

# Создаем глобальный экземпляр клиента
clickhouse_client = ClickHouseClient()
