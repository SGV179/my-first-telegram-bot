import logging
from app.database.db_connection import db
from app.config.config import config

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def create_or_update_user(telegram_id: int, username: str = None, 
                            first_name: str = None, last_name: str = None):
        """Create or update user in database"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (telegram_id) 
                DO UPDATE SET 
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name
                RETURNING id
            """, (telegram_id, username, first_name, last_name))
            
            result = cursor.fetchone()
            conn.commit()
            cursor.close()
            
            logger.info(f"✅ User {telegram_id} created/updated successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error creating/updating user {telegram_id}: {e}")
            return None

    @staticmethod
    def get_user(telegram_id: int):
        """Get user by telegram ID"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, telegram_id, username, first_name, last_name, 
                       role, points, referral_code, referred_by, is_active,
                       subscribed_to_bot, subscribed_channel_1, subscribed_channel_2,
                       welcome_points_given, created_at
                FROM users 
                WHERE telegram_id = %s
            """, (telegram_id,))
            
            user = cursor.fetchone()
            cursor.close()
            
            return user
            
        except Exception as e:
            logger.error(f"❌ Error getting user {telegram_id}: {e}")
            return None

    @staticmethod
    def update_subscription_status(telegram_id: int, channel_1: bool = None, 
                                 channel_2: bool = None, bot_subscribed: bool = None):
        """Update user subscription status"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            update_fields = []
            params = []
            
            if channel_1 is not None:
                update_fields.append("subscribed_channel_1 = %s")
                params.append(channel_1)
            if channel_2 is not None:
                update_fields.append("subscribed_channel_2 = %s")
                params.append(channel_2)
            if bot_subscribed is not None:
                update_fields.append("subscribed_to_bot = %s")
                params.append(bot_subscribed)
            
            if update_fields:
                params.append(telegram_id)
                
                cursor.execute(f"""
                    UPDATE users 
                    SET {', '.join(update_fields)}
                    WHERE telegram_id = %s
                """, params)
                
                conn.commit()
            
            cursor.close()
            logger.info(f"✅ Subscription status updated for user {telegram_id}")
            
        except Exception as e:
            logger.error(f"❌ Error updating subscription status for user {telegram_id}: {e}")

    @staticmethod
    def check_user_subscriptions(telegram_id: int):
        """Check if user is subscribed to both channels"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT subscribed_channel_1, subscribed_channel_2, subscribed_to_bot
                FROM users 
                WHERE telegram_id = %s
            """, (telegram_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return {
                    'channel_1': result[0],
                    'channel_2': result[1],
                    'bot': result[2]
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking subscriptions for user {telegram_id}: {e}")
            return None

    @staticmethod
    def give_welcome_points(telegram_id: int):
        """Give welcome points to user if eligible"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Check if user already received welcome points
            cursor.execute("""
                SELECT welcome_points_given, subscribed_channel_1, subscribed_channel_2
                FROM users 
                WHERE telegram_id = %s
            """, (telegram_id,))
            
            user = cursor.fetchone()
            
            if user and not user[0] and user[1] and user[2]:  # Not given yet and subscribed to both channels
                # Get welcome points amount from settings
                cursor.execute("""
                    SELECT setting_value FROM loyalty_settings 
                    WHERE setting_name = 'welcome_points'
                """)
                welcome_points = cursor.fetchone()[0]
                
                # Update user points and mark as given
                cursor.execute("""
                    UPDATE users 
                    SET points = points + %s, 
                        welcome_points_given = TRUE
                    WHERE telegram_id = %s
                """, (welcome_points, telegram_id))
                
                # Log transaction
                cursor.execute("""
                    INSERT INTO points_transactions 
                    (user_id, transaction_type, points_change, description)
                    VALUES (%s, 'welcome_bonus', %s, 'Welcome points for subscribing to both channels')
                """, (telegram_id, welcome_points))
                
                conn.commit()
                cursor.close()
                
                logger.info(f"✅ Welcome points given to user {telegram_id}")
                return welcome_points
            
            cursor.close()
            return 0
            
        except Exception as e:
            logger.error(f"❌ Error giving welcome points to user {telegram_id}: {e}")
            return 0
