import logging
from datetime import datetime
from app.database.db_connection import db
from app.services.points_service import PointsService

logger = logging.getLogger(__name__)

class ActivityService:
    @staticmethod
    def track_activity(user_id: int, activity_type: str, channel_id: int = None, 
                      message_id: int = None, description: str = None):
        """Track user activity and award points"""
        try:
            # Get points for this activity type from loyalty settings
            loyalty_settings = PointsService.get_loyalty_settings()
            points = loyalty_settings.get(f"{activity_type}_points", 0)
            
            if points == 0:
                logger.info(f"⚠️ No points configured for activity: {activity_type}")
                return False
            
            # Check if this activity was already tracked (prevent duplicates)
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if message_id:
                cursor.execute("""
                    SELECT id FROM activity_logs 
                    WHERE user_id = %s AND activity_type = %s AND message_id = %s
                    LIMIT 1
                """, (user_id, activity_type, message_id))
                
                if cursor.fetchone():
                    cursor.close()
                    logger.info(f"⚠️ Activity already tracked: {activity_type} for user {user_id}")
                    return False
            
            # Add points to user
            success = PointsService.add_points(
                user_id, 
                activity_type, 
                points, 
                description,
                channel_id,
                message_id
            )
            
            cursor.close()
            
            if success:
                logger.info(f"✅ Tracked {activity_type} for user {user_id}: +{points} points")
            else:
                logger.error(f"❌ Failed to track {activity_type} for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error tracking activity for user {user_id}: {e}")
            return False

    @staticmethod
    def remove_activity_points(user_id: int, activity_type: str, message_id: int = None):
        """Remove points for undone activity (like unlike, comment delete)"""
        try:
            # Get points for this activity type
            loyalty_settings = PointsService.get_loyalty_settings()
            points = loyalty_settings.get(f"{activity_type}_points", 0)
            
            if points == 0:
                return False
            
            # Remove points from user
            description = f"Отмена активности: {activity_type}"
            success = PointsService.remove_points(user_id, activity_type, points, description)
            
            if success:
                logger.info(f"✅ Removed {activity_type} points for user {user_id}: -{points} points")
            else:
                logger.error(f"❌ Failed to remove {activity_type} points for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error removing activity points for user {user_id}: {e}")
            return False

    @staticmethod
    def get_user_activities(user_id: int, limit: int = 10):
        """Get user activity history"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT activity_type, points_earned, channel_id, created_at
                FROM activity_logs 
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, limit))
            
            activities = cursor.fetchall()
            cursor.close()
            
            return activities
            
        except Exception as e:
            logger.error(f"❌ Error getting activities for user {user_id}: {e}")
            return []

    @staticmethod
    def get_activities_stats(days: int = 7):
        """Get activities statistics for period"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    activity_type,
                    COUNT(*) as count,
                    SUM(points_earned) as total_points
                FROM activity_logs 
                WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY activity_type
                ORDER BY count DESC
            """, (days,))
            
            stats = cursor.fetchall()
            cursor.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting activities stats: {e}")
            return []

    @staticmethod
    def get_top_active_users(limit: int = 10, days: int = 30):
        """Get most active users"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    u.telegram_id,
                    u.username,
                    u.first_name,
                    COUNT(al.id) as activity_count,
                    SUM(al.points_earned) as total_points
                FROM activity_logs al
                JOIN users u ON al.user_id = u.telegram_id
                WHERE al.created_at >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY u.telegram_id, u.username, u.first_name
                ORDER BY activity_count DESC
                LIMIT %s
            """, (days, limit))
            
            top_users = cursor.fetchall()
            cursor.close()
            
            return top_users
            
        except Exception as e:
            logger.error(f"❌ Error getting top active users: {e}")
            return []
