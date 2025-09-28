from analytics.clickhouse_client import clickhouse_client

class AnalyticsManager:
    def __init__(self):
        self.client = clickhouse_client
        self._create_tables()
    
    def _create_tables(self):
        """Создает таблицы для хранения событий аналитики"""
        
        # Таблица событий пользователей
        user_events_table = """
        CREATE TABLE IF NOT EXISTS user_events (
            event_date Date DEFAULT today(),
            event_time DateTime DEFAULT now(),
            user_id Int64,
            event_type String,
            channel_id Int64,
            post_id Nullable(Int64),
            comment_id Nullable(Int64),
            action_data String,
            score_change Int32 DEFAULT 0
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(event_date)
        ORDER BY (event_date, user_id, event_type)
        """
        
        # Таблица ежедневной статистики
        daily_stats_table = """
        CREATE TABLE IF NOT EXISTS daily_stats (
            stat_date Date DEFAULT today(),
            channel_id Int64,
            total_users Int64,
            new_users Int64,
            active_users Int64,
            total_likes Int64,
            total_comments Int64,
            total_reposts Int64
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(stat_date)
        ORDER BY (stat_date, channel_id)
        """
        
        try:
            self.client.execute(user_events_table)
            self.client.execute(daily_stats_table)
            print("✅ Таблицы аналитики в ClickHouse созданы")
        except Exception as e:
            print(f"❌ Ошибка создания таблиц: {e}")

# Создаем менеджер аналитики
analytics_manager = AnalyticsManager()
