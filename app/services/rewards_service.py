import logging
from app.services.file_service import FileService
from app.database.db_connection import db

logger = logging.getLogger(__name__)

class RewardsService:
    @staticmethod
    def create_reward(title: str, description: str, cost_points: int, pdf_file_id: str = None):
        """Create new reward"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO rewards (title, description, cost_points, pdf_file_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (title, description, cost_points, pdf_file_id))
            
            reward_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            logger.info(f"✅ Reward created: {title} (ID: {reward_id})")
            return reward_id
            
        except Exception as e:
            logger.error(f"❌ Error creating reward: {e}")
            return None

    @staticmethod
    def get_all_rewards(only_active: bool = True):
        """Get all rewards"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if only_active:
                cursor.execute("""
                    SELECT id, title, description, cost_points, pdf_file_id
                    FROM rewards 
                    WHERE is_active = TRUE
                    ORDER BY cost_points
                """)
            else:
                cursor.execute("""
                    SELECT id, title, description, cost_points, pdf_file_id, is_active
                    FROM rewards 
                    ORDER BY cost_points
                """)
            
            rewards = cursor.fetchall()
            cursor.close()
            
            return rewards
            
        except Exception as e:
            logger.error(f"❌ Error getting rewards: {e}")
            return []

    @staticmethod
    def get_reward(reward_id: int):
        """Get reward by ID"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, description, cost_points, pdf_file_id, is_active
                FROM rewards 
                WHERE id = %s
            """, (reward_id,))
            
            reward = cursor.fetchone()
            cursor.close()
            
            return reward
            
        except Exception as e:
            logger.error(f"❌ Error getting reward {reward_id}: {e}")
            return None

    @staticmethod
    def update_reward(reward_id: int, title: str = None, description: str = None, 
                     cost_points: int = None, is_active: bool = None):
        """Update reward"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            update_fields = []
            params = []
            
            if title is not None:
                update_fields.append("title = %s")
                params.append(title)
            if description is not None:
                update_fields.append("description = %s")
                params.append(description)
            if cost_points is not None:
                update_fields.append("cost_points = %s")
                params.append(cost_points)
            if is_active is not None:
                update_fields.append("is_active = %s")
                params.append(is_active)
            
            if update_fields:
                params.append(reward_id)
                
                cursor.execute(f"""
                    UPDATE rewards 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """, params)
                
                conn.commit()
            
            cursor.close()
            logger.info(f"✅ Reward {reward_id} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating reward {reward_id}: {e}")
            return False

    @staticmethod
    def delete_reward(reward_id: int):
        """Delete reward (soft delete)"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE rewards 
                SET is_active = FALSE
                WHERE id = %s
            """, (reward_id,))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"✅ Reward {reward_id} deleted (deactivated)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting reward {reward_id}: {e}")
            return False

    @staticmethod
    async def purchase_reward(bot, user_id: int, reward_id: int):
        """Purchase reward for user and send PDF if available"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get reward details
            cursor.execute("""
                SELECT title, cost_points, pdf_file_id 
                FROM rewards 
                WHERE id = %s AND is_active = TRUE
            """, (reward_id,))
            
            reward = cursor.fetchone()
            
            if not reward:
                cursor.close()
                return False, "Награда не найдена или недоступна", None
            
            reward_title, cost_points, pdf_file_id = reward
            
            # Check user points
            cursor.execute("SELECT points FROM users WHERE telegram_id = %s", (user_id,))
            user_points = cursor.fetchone()[0]
            
            if user_points < cost_points:
                cursor.close()
                return False, f"Недостаточно баллов. Нужно: {cost_points}, у вас: {user_points}", None
            
            # Deduct points and create purchase record
            cursor.execute("""
                UPDATE users 
                SET points = points - %s
                WHERE telegram_id = %s
            """, (cost_points, user_id))
            
            cursor.execute("""
                INSERT INTO user_rewards (user_id, reward_id, points_spent)
                VALUES (%s, %s, %s)
            """, (user_id, reward_id, cost_points))
            
            # Log transaction
            cursor.execute("""
                INSERT INTO points_transactions 
                (user_id, transaction_type, points_change, description)
                VALUES (%s, 'reward_purchase', %s, %s)
            """, (user_id, -cost_points, f"Покупка награды: {reward_title}"))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"✅ User {user_id} purchased reward {reward_id} for {cost_points} points")
            
            # Return success with reward details
            return True, reward_title, pdf_file_id
            
        except Exception as e:
            logger.error(f"❌ Error purchasing reward {reward_id} for user {user_id}: {e}")
            return False, "Произошла ошибка при покупке", None

    @staticmethod
    def get_user_rewards(user_id: int):
        """Get rewards purchased by user"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT r.title, r.description, ur.points_spent, ur.purchased_at
                FROM user_rewards ur
                JOIN rewards r ON ur.reward_id = r.id
                WHERE ur.user_id = %s
                ORDER BY ur.purchased_at DESC
            """, (user_id,))
            
            rewards = cursor.fetchall()
            cursor.close()
            
            return rewards
            
        except Exception as e:
            logger.error(f"❌ Error getting user rewards for {user_id}: {e}")
            return []
