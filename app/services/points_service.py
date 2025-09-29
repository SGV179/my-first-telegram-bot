import logging
from app.database.db_connection import db

logger = logging.getLogger(__name__)

class PointsService:
    @staticmethod
    def add_points(telegram_id: int, activity_type: str, points: int, 
                  description: str = None, channel_id: int = None, message_id: int = None):
        """Add points to user for specific activity"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Update user points
            cursor.execute("""
                UPDATE users 
                SET points = points + %s, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = %s AND is_active = TRUE
            """, (points, telegram_id))
            
            # Log points transaction
            cursor.execute("""
                INSERT INTO points_transactions 
                (user_id, transaction_type, points_change, description)
                VALUES (%s, %s, %s, %s)
            """, (telegram_id, activity_type, points, description))
            
            # Log activity
            cursor.execute("""
                INSERT INTO activity_logs 
                (user_id, activity_type, channel_id, message_id, points_earned)
                VALUES (%s, %s, %s, %s, %s)
            """, (telegram_id, activity_type, channel_id, message_id, points))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"✅ Added {points} points to user {telegram_id} for {activity_type}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding points to user {telegram_id}: {e}")
            return False

    @staticmethod
    def remove_points(telegram_id: int, activity_type: str, points: int, description: str = None):
        """Remove points from user (for undo actions)"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Update user points
            cursor.execute("""
                UPDATE users 
                SET points = points - %s, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = %s AND is_active = TRUE
            """, (points, telegram_id))
            
            # Log points transaction
            cursor.execute("""
                INSERT INTO points_transactions 
                (user_id, transaction_type, points_change, description)
                VALUES (%s, %s, %s, %s)
            """, (telegram_id, activity_type, -points, description))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"✅ Removed {points} points from user {telegram_id} for {activity_type}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error removing points from user {telegram_id}: {e}")
            return False

    @staticmethod
    def get_loyalty_settings():
        """Get current loyalty program settings"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT setting_name, setting_value, description 
                FROM loyalty_settings
            """)
            
            settings = cursor.fetchall()
            cursor.close()
            
            return {setting[0]: setting[1] for setting in settings}
            
        except Exception as e:
            logger.error(f"❌ Error getting loyalty settings: {e}")
            return {}

    @staticmethod
    def update_loyalty_setting(setting_name: str, new_value: int):
        """Update loyalty program setting"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE loyalty_settings 
                SET setting_value = %s, updated_at = CURRENT_TIMESTAMP
                WHERE setting_name = %s
            """, (new_value, setting_name))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"✅ Updated loyalty setting {setting_name} to {new_value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating loyalty setting {setting_name}: {e}")
            return False

    @staticmethod
    def get_user_points(telegram_id: int):
        """Get user current points"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT points FROM users WHERE telegram_id = %s
            """, (telegram_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"❌ Error getting points for user {telegram_id}: {e}")
            return 0

    @staticmethod
    def get_user_transactions(telegram_id: int, limit: int = 10):
        """Get user points transactions history"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT transaction_type, points_change, description, created_at
                FROM points_transactions 
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (telegram_id, limit))
            
            transactions = cursor.fetchall()
            cursor.close()
            
            return transactions
            
        except Exception as e:
            logger.error(f"❌ Error getting transactions for user {telegram_id}: {e}")
            return []
