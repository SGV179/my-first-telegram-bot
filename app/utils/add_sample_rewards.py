import logging
from app.database.db_connection import db
from app.utils.logger import logger

def add_sample_rewards():
    """Add sample rewards to database"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if rewards already exist
        cursor.execute("SELECT COUNT(*) FROM rewards WHERE is_active = TRUE")
        count = cursor.fetchone()[0]
        
        if count > 0:
            logger.info("✅ Sample rewards already exist")
            return
        
        # Add sample rewards with placeholder file IDs (will be replaced with actual files)
        sample_rewards = [
            {
                'title': '📚 Электронная книга "Основы инвестирования"',
                'description': 'Подробное руководство для начинающих инвесторов с примерами и стратегиями',
                'cost_points': 50,
                'pdf_file_id': 'sample_investment_guide'
            },
            {
                'title': '🎓 Видео-курс "Финансовая грамотность"',
                'description': '5 уроков по управлению личными финансами и планированию бюджета',
                'cost_points': 100,
                'pdf_file_id': 'sample_financial_course'
            },
            {
                'title': '📊 Шаблон Excel для учета финансов',
                'description': 'Удобный шаблон для отслеживания доходов и расходов с автоматическими отчетами',
                'cost_points': 30,
                'pdf_file_id': 'sample_excel_template'
            },
            {
                'title': '💼 Консультация с экспертом',
                'description': '30-минутная онлайн-консультация по вопросам инвестиций и финансового планирования',
                'cost_points': 200,
                'pdf_file_id': None  # This reward doesn't have a PDF
            },
            {
                'title': '📈 Доступ к эксклюзивным материалам',
                'description': 'Закрытые аналитические отчеты и прогнозы рынка',
                'cost_points': 150,
                'pdf_file_id': 'sample_exclusive_reports'
            }
        ]
        
        for reward in sample_rewards:
            cursor.execute("""
                INSERT INTO rewards (title, description, cost_points, pdf_file_id)
                VALUES (%s, %s, %s, %s)
            """, (reward['title'], reward['description'], reward['cost_points'], reward['pdf_file_id']))
        
        conn.commit()
        cursor.close()
        
        logger.info("✅ Sample rewards with PDF files added successfully")
        
    except Exception as e:
        logger.error(f"❌ Error adding sample rewards: {e}")

if __name__ == "__main__":
    add_sample_rewards()
