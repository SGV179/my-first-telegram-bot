import logging
from aiogram.types import ChatMemberUpdated, MessageReactionUpdated, Message
from app.services.activity_service import ActivityService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

class ChannelEventsService:
    @staticmethod
    async def handle_reaction_update(event: MessageReactionUpdated):
        """Handle message reaction updates in channels"""
        try:
            user_id = event.user.id
            channel_id = event.chat.id
            
            # Check if user exists and is active
            user = UserService.get_user(user_id)
            if not user or not user[9]:  # is_active field
                return
            
            # Check if this is our tracked channel
            from app.config.config import config
            if channel_id not in [config.CHANNEL_1_ID, config.CHANNEL_2_ID]:
                return
            
            # Track like activity
            if event.old_reaction and not event.new_reaction:
                # Reaction removed (unlike)
                ActivityService.remove_activity_points(
                    user_id, 
                    'like', 
                    event.message_id
                )
                logger.info(f"🔄 Like removed by user {user_id} in channel {channel_id}")
                
            elif event.new_reaction and not event.old_reaction:
                # New reaction (like)
                ActivityService.track_activity(
                    user_id,
                    'like',
                    channel_id,
                    event.message_id,
                    f"Лайк в канале {channel_id}"
                )
                logger.info(f"❤️ Like tracked for user {user_id} in channel {channel_id}")
                
        except Exception as e:
            logger.error(f"❌ Error handling reaction update: {e}")

    @staticmethod
    async def handle_channel_post(message: Message):
        """Handle new messages in channels (for comments tracking)"""
        try:
            # This would require the bot to be admin in the channel
            # and have permissions to see messages
            pass
            
        except Exception as e:
            logger.error(f"❌ Error handling channel post: {e}")

    @staticmethod
    async def handle_chat_member_update(update: ChatMemberUpdated):
        """Handle chat member updates (for subscription tracking)"""
        try:
            user_id = update.new_chat_member.user.id
            channel_id = update.chat.id
            
            # Check if this is our tracked channel
            from app.config.config import config
            if channel_id not in [config.CHANNEL_1_ID, config.CHANNEL_2_ID]:
                return
            
            # Update user subscription status
            is_member = update.new_chat_member.status in ['member', 'administrator', 'creator']
            
            if channel_id == config.CHANNEL_1_ID:
                UserService.update_subscription_status(
                    telegram_id=user_id,
                    channel_1=is_member
                )
            elif channel_id == config.CHANNEL_2_ID:
                UserService.update_subscription_status(
                    telegram_id=user_id,
                    channel_2=is_member
                )
            
            logger.info(f"📺 Subscription updated for user {user_id} in channel {channel_id}: {is_member}")
            
        except Exception as e:
            logger.error(f"❌ Error handling chat member update: {e}")
