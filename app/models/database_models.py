from app.services.file_service import FileService
from app.utils.add_sample_rewards import add_sample_rewards
from datetime import datetime
from app.database.db_connection import db
import logging

logger = logging.getLogger(__name__)

def init_database():
    """Initialize database tables if they don't exist"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            )
        """)
        tables_exist = cursor.fetchone()[0]
        
        if tables_exist:
            logger.info("✅ Database tables already exist")
            cursor.close()
            return
        
        # Users table
        cursor.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'user',
                points INTEGER DEFAULT 0,
                referral_code VARCHAR(50) UNIQUE,
                referred_by BIGINT,
                is_active BOOLEAN DEFAULT TRUE,
                subscribed_to_bot BOOLEAN DEFAULT TRUE,
                subscribed_channel_1 BOOLEAN DEFAULT FALSE,
                subscribed_channel_2 BOOLEAN DEFAULT FALSE,
                welcome_points_given BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Points transactions table
        cursor.execute("""
            CREATE TABLE points_transactions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                transaction_type VARCHAR(100) NOT NULL,
                points_change INTEGER NOT NULL,
                description TEXT,
                related_entity_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Rewards table
        cursor.execute("""
            CREATE TABLE rewards (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                pdf_file_id VARCHAR(255),
                cost_points INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User rewards table
        cursor.execute("""
            CREATE TABLE user_rewards (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                reward_id INTEGER NOT NULL,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                points_spent INTEGER NOT NULL
            )
        """)
        
        # Activity logs table
        cursor.execute("""
            CREATE TABLE activity_logs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                activity_type VARCHAR(100) NOT NULL,
                channel_id BIGINT,
                message_id BIGINT,
                points_earned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Loyalty settings table
        cursor.execute("""
            CREATE TABLE loyalty_settings (
                id SERIAL PRIMARY KEY,
                setting_name VARCHAR(100) UNIQUE NOT NULL,
                setting_value INTEGER NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default loyalty settings
        cursor.execute("""
            INSERT INTO loyalty_settings (setting_name, setting_value, description) 
            VALUES 
            ('welcome_points', 30, 'Points for welcome subscription'),
            ('comment_points', 5, 'Points for comment'),
            ('repost_points', 3, 'Points for repost'),
            ('like_points', 1, 'Points for like'),
            ('button_click_points', 10, 'Points for button click'),
            ('referral_points', 50, 'Points for referral')
            ON CONFLICT (setting_name) DO NOTHING
        """)
        
        # Add sample rewards only if they don't exist
        cursor.execute("SELECT COUNT(*) FROM rewards")
        rewards_count = cursor.fetchone()[0]
        
        if rewards_count == 0:
            sample_rewards = [
                ('📚 Электронная книга "Основы инвестирования"', 'Подробное руководство для начинающих инвесторов с примерами и стратегиями', 50, 'sample_investment_guide'),
                ('🎓 Видео-курс "Финансовая грамотность"', '5 уроков по управлению личными финансами и планированию бюджета', 100, 'sample_financial_course'),
                ('📊 Шаблон Excel для учета финансов', 'Удобный шаблон для отслеживания доходов и расходов с автоматическими отчетами', 30, 'sample_excel_template'),
                ('💼 Консультация с экспертом', '30-минутная онлайн-консультация по вопросам инвестиций и финансового планирования', 200, None),
                ('📈 Доступ к эксклюзивным материалам', 'Закрытые аналитические отчеты и прогнозы рынка', 150, 'sample_exclusive_reports')
            ]
            
            for reward in sample_rewards:
                cursor.execute("""
                    INSERT INTO rewards (title, description, cost_points, pdf_file_id)
                    VALUES (%s, %s, %s, %s)
                """, reward)
            
            logger.info("✅ Sample rewards added")
        
        conn.commit()
        cursor.close()
        
        # Create sample PDF files
        from app.services.file_service import FileService
        FileService.create_sample_pdf_files()
        
        logger.info("✅ Database tables initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        raise
