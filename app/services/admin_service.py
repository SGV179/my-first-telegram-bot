import logging
from app.database.db_connection import db
from app.config.config import config

logger = logging.getLogger(__name__)

class AdminService:
    @staticmethod
    def is_admin(user_id: int):
        """Check if user is admin"""
        return user_id in config.ADMIN_IDS

    @staticmethod
    def get_all_users(limit: int = 100, offset: int = 0):
        """Get all users with pagination"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT telegram_id, username, first_name, last_name, 
                       role, points, is_active, subscribed_to_bot,
                       subscribed_channel_1, subscribed_channel_2,
                       created_at
                FROM users 
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            users = cursor.fetchall()
            cursor.close()
            
            return users
            
        except Exception as e:
            logger.error(f"❌ Error getting users: {e}")
            return []

    @staticmethod
    def get_users_count():
        """Get total users count"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            cursor.close()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error getting users count: {e}")
            return 0

    @staticmethod
    def get_user_stats():
        """Get users statistics"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            # Active users
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
            active_users = cursor.fetchone()[0]
            
            # Users subscribed to bot
            cursor.execute("SELECT COUNT(*) FROM users WHERE subscribed_to_bot = TRUE")
            bot_subscribers = cursor.fetchone()[0]
            
            # Users subscribed to both channels
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE subscribed_channel_1 = TRUE AND subscribed_channel_2 = TRUE
            """)
            channel_subscribers = cursor.fetchone()[0]
            
            # Total points in system
            cursor.execute("SELECT COALESCE(SUM(points), 0) FROM users")
            total_points = cursor.fetchone()[0]
            
            cursor.close()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'bot_subscribers': bot_subscribers,
                'channel_subscribers': channel_subscribers,
                'total_points': total_points
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user stats: {e}")
            return {}

    @staticmethod
    def update_user_points(telegram_id: int, new_points: int):
        """Update user points (admin function)"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get current points
            cursor.execute("SELECT points FROM users WHERE telegram_id = %s", (telegram_id,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                return False, "Пользователь не найден"
            
            current_points = result[0]
            points_change = new_points - current_points
            
            # Update points
            cursor.execute("""
                UPDATE users 
                SET points = %s
                WHERE telegram_id = %s
            """, (new_points, telegram_id))
            
            # Log transaction if points changed
            if points_change != 0:
                cursor.execute("""
                    INSERT INTO points_transactions 
                    (user_id, transaction_type, points_change, description)
                    VALUES (%s, 'admin_adjustment', %s, %s)
                """, (telegram_id, points_change, "Корректировка баллов администратором"))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"✅ Admin updated points for user {telegram_id}: {current_points} -> {new_points}")
            return True, f"Баллы обновлены: {current_points} → {new_points}"
            
        except Exception as e:
            logger.error(f"❌ Error updating user points {telegram_id}: {e}")
            return False, "Ошибка при обновлении баллов"

    @staticmethod
    def add_points_to_user(telegram_id: int, points_to_add: int, reason: str = ""):
        """Add points to user (admin function)"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT points FROM users WHERE telegram_id = %s", (telegram_id,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                return False, "Пользователь не найден"
            
            current_points = result[0]
            new_points = current_points + points_to_add
            
            # Update points
            cursor.execute("""
                UPDATE users 
                SET points = %s
                WHERE telegram_id = %s
            """, (new_points, telegram_id))
            
            # Log transaction
            description = f"Начисление баллов администратором: {reason}" if reason else "Начисление баллов администратором"
            cursor.execute("""
                INSERT INTO points_transactions 
                (user_id, transaction_type, points_change, description)
                VALUES (%s, 'admin_bonus', %s, %s)
            """, (telegram_id, points_to_add, description))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"✅ Admin added {points_to_add} points to user {telegram_id}")
            return True, f"Начислено {points_to_add} баллов. Новый баланс: {new_points}"
            
        except Exception as e:
            logger.error(f"❌ Error adding points to user {telegram_id}: {e}")
            return False, "Ошибка при начислении баллов"

    @staticmethod
    def get_system_stats():
        """Get comprehensive system statistics"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Rewards statistics
            cursor.execute("""
                SELECT COUNT(*) as total_rewards,
                       COUNT(*) FILTER (WHERE is_active = TRUE) as active_rewards,
                       COALESCE(SUM(cost_points), 0) as total_rewards_cost
                FROM rewards
            """)
            rewards_stats = cursor.fetchone()
            
            # Transactions statistics
            cursor.execute("""
                SELECT COUNT(*) as total_transactions,
                       COALESCE(SUM(points_change), 0) as total_points_movement
                FROM points_transactions
            """)
            transactions_stats = cursor.fetchone()
            
            # Recent activities
            cursor.execute("""
                SELECT activity_type, COUNT(*) as count
                FROM activity_logs 
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY activity_type
                ORDER BY count DESC
            """)
            recent_activities = cursor.fetchall()
            
            cursor.close()
            
            return {
                'rewards': {
                    'total': rewards_stats[0],
                    'active': rewards_stats[1],
                    'total_cost': rewards_stats[2]
                },
                'transactions': {
                    'total': transactions_stats[0],
                    'total_points': transactions_stats[1]
                },
                'recent_activities': dict(recent_activities)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting system stats: {e}")
            return {}
