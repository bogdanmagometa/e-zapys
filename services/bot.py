import logging
import asyncio
import threading
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logger = logging.getLogger(__name__)

# Callback data prefixes
CB_TOGGLE_CENTER = "toggle:"
CB_SELECT_ALL = "select_all"
CB_DESELECT_ALL = "deselect_all"
CB_SAVE = "save"


class BotService:
    def __init__(self, bot_token: str, db, message_service):
        self.bot_token = bot_token
        self.db = db
        self.users_collection = self.db['users']
        self.message_service = message_service
        self.application = None
        self.bot_thread = None
        self.loop = None
        
    def start(self):
        """Start the bot"""
        logger.info("Starting Telegram bot...")
        
        # Create the Application and pass it your bot's token
        self.application = Application.builder().token(self.bot_token).build()
        
        # Track all interactions (commands and messages) to register users
        self.application.add_handler(MessageHandler(filters.ALL, self._track_user), group=-1)
        
        # Register command handlers
        self.application.add_handler(CommandHandler("start", self._help))
        self.application.add_handler(CommandHandler("help", self._help))
        self.application.add_handler(CommandHandler("availability", self._availability))
        self.application.add_handler(CommandHandler("change_subscription", self._change_subscription))
        self.application.add_handler(CommandHandler("status", self._status))
        
        # Register callback query handler for inline keyboard
        self.application.add_handler(CallbackQueryHandler(self._subscription_callback))
        
        # Start the bot in a separate thread
        def run_bot():
            """Run the bot in a separate event loop"""
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Start polling without signal handlers (since we're in a thread)
            # stop_signals=None disables signal handling which only works in main thread
            self.loop.run_until_complete(
                self.application.run_polling(stop_signals=None)
            )
        
        self.bot_thread = threading.Thread(target=run_bot, daemon=True)
        self.bot_thread.start()
        
        # Give the bot a moment to start
        import time
        time.sleep(1)
        
        logger.info("Telegram bot started successfully!")
    
    def stop(self):
        """Stop the bot"""
        if self.application and self.loop:
            logger.info("Stopping Telegram bot...")
            
            # Stop the bot gracefully
            asyncio.run_coroutine_threadsafe(self.application.stop(), self.loop)
            asyncio.run_coroutine_threadsafe(self.application.shutdown(), self.loop)
            
            # Wait a bit for cleanup
            import time
            time.sleep(1)
            
            logger.info("Telegram bot stopped successfully!")
    
    def broadcast_availability_changes(self, changes: dict):
        """
        Broadcast availability changes to users based on their subscribed centers.
        Each user receives a personalized notification for only their subscribed centers.
        
        Args:
            changes: Dict with 'added' and 'removed' lists of center data
        """
        logger.info("broadcast_availability_changes called")
        
        if not self.loop or not self.application:
            logger.warning("Bot not initialized, cannot broadcast message")
            return
        
        # Schedule the async broadcast in the bot's event loop
        future = asyncio.run_coroutine_threadsafe(
            self._broadcast_availability_changes_async(changes),
            self.loop
        )
        
        try:
            future.result(timeout=60)  # 60 second timeout for personalized messages
            logger.info("Availability broadcast completed successfully")
        except Exception as e:
            logger.error(f"Error broadcasting availability changes: {e}", exc_info=True)
    
    async def _broadcast_availability_changes_async(self, changes: dict):
        """
        Async method to send personalized availability notifications.
        """
        added_centers = changes.get('added', [])
        removed_centers = changes.get('removed', [])
        
        # Get center names that changed
        added_names = {c['center'] for c in added_centers}
        removed_names = {c['center'] for c in removed_centers}
        all_changed_names = added_names | removed_names
        
        # Get users who have at least one subscribed center in the changed centers
        users_cursor = self.users_collection.find({
            'subscribed_centers': {'$in': list(all_changed_names)}
        })
        users = list(users_cursor)
        
        logger.info(f"Found {len(users)} users subscribed to changed centers")
        
        if not users:
            logger.info("No users subscribed to the changed centers")
            return
        
        sent_count = 0
        error_count = 0
        
        for user in users:
            chat_id = user['chat_id']
            username = user.get('username', 'Unknown')
            user_centers = set(user.get('subscribed_centers', []))
            
            # Filter changes to only include this user's subscribed centers
            user_added = [c for c in added_centers if c['center'] in user_centers]
            user_removed = [c for c in removed_centers if c['center'] in user_centers]
            
            if not user_added and not user_removed:
                continue
            
            # Format personalized message
            user_changes = {'added': user_added, 'removed': user_removed}
            message = self.message_service.availability_changed(user_changes)
            
            try:
                await self.application.bot.send_message(chat_id=chat_id, text=message)
                sent_count += 1
                logger.debug(f"Sent notification to {username}: {len(user_added)} added, {len(user_removed)} removed")
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to send message to {chat_id}: {e}")
        
        logger.info(f"Availability broadcast complete: {sent_count} sent, {error_count} failed")
    
    async def _track_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Track users who interact with the bot (via commands or messages)"""
        if update.effective_user and update.effective_chat:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            username = update.effective_user.username
            first_name = update.effective_user.first_name
            last_name = update.effective_user.last_name
            
            # Upsert user in MongoDB
            self.users_collection.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'chat_id': chat_id,
                        'username': username,
                        'first_name': first_name,
                        'last_name': last_name,
                        'last_interaction': datetime.utcnow()
                    },
                    '$setOnInsert': {
                        'first_seen': datetime.utcnow(),
                        'subscribed_centers': []  # Default to no subscriptions
                    }
                },
                upsert=True
            )
            logger.debug(f"Tracked user: {user_id} ({username or first_name})")
    
    async def _help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command"""
        await update.message.reply_text(self.message_service.help())
    
    async def _availability(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /availability command"""
        from dependencies import get_availability_service
        availability_service = get_availability_service()
        
        availability_data = availability_service.get_availability()
        await update.message.reply_text(self.message_service.availability(availability_data))
    
    async def _change_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /change_subscription command - show center selection UI"""
        user_id = update.effective_user.id
        
        # Get all centers from availability collection (need both center name and address)
        from dependencies import get_availability_service
        availability_service = get_availability_service()
        all_centers = list(availability_service.db['availability'].find({}, {'center': 1, 'address': 1, '_id': 0}))
        
        if not all_centers:
            await update.message.reply_text(self.message_service.subscription_no_centers())
            return
        
        # Get user's current subscriptions
        user = self.users_collection.find_one({'user_id': user_id})
        current_subscriptions = set(user.get('subscribed_centers', []) if user else [])
        
        # Store state in context.user_data (list of dicts with center and address)
        context.user_data['subscription_centers'] = all_centers
        context.user_data['selected_centers'] = current_subscriptions.copy()
        
        # Build and send keyboard
        keyboard = self._build_subscription_keyboard(all_centers, current_subscriptions)
        text = self.message_service.subscription_prompt(len(current_subscriptions), len(all_centers))
        
        await update.message.reply_text(text, reply_markup=keyboard)
    
    def _build_subscription_keyboard(self, all_centers: list, selected: set) -> InlineKeyboardMarkup:
        """Build inline keyboard for subscription selection"""
        keyboard = []
        
        # Add center buttons (one per row for readability)
        # Use index in callback_data since Telegram has 64-byte limit
        for idx, center_data in enumerate(all_centers):
            center_name = center_data['center']
            address = center_data.get('address', center_name)
            emoji = "✅" if center_name in selected else "⬜"
            # Truncate long addresses for display
            display_text = address[:35] + "..." if len(address) > 38 else address
            keyboard.append([
                InlineKeyboardButton(f"{emoji} {display_text}", callback_data=f"{CB_TOGGLE_CENTER}{idx}")
            ])
        
        # Add control buttons
        keyboard.append([
            InlineKeyboardButton("✅ Обрати всі", callback_data=CB_SELECT_ALL),
            InlineKeyboardButton("⬜ Зняти всі", callback_data=CB_DESELECT_ALL)
        ])
        keyboard.append([
            InlineKeyboardButton("💾 Зберегти", callback_data=CB_SAVE)
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _subscription_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from subscription inline keyboard"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        all_centers = context.user_data.get('subscription_centers', [])
        selected = context.user_data.get('selected_centers', set())
        
        if not all_centers:
            await query.edit_message_text(self.message_service.subscription_session_expired())
            return
        
        if data.startswith(CB_TOGGLE_CENTER):
            # Toggle specific center by index
            try:
                center_idx = int(data[len(CB_TOGGLE_CENTER):])
                center_name = all_centers[center_idx]['center']
                if center_name in selected:
                    selected.discard(center_name)
                else:
                    selected.add(center_name)
                context.user_data['selected_centers'] = selected
            except (ValueError, IndexError, KeyError):
                logger.error(f"Invalid center index in callback: {data}")
                return
            
        elif data == CB_SELECT_ALL:
            # Select all centers
            selected = set(c['center'] for c in all_centers)
            context.user_data['selected_centers'] = selected
            
        elif data == CB_DESELECT_ALL:
            # Deselect all centers
            selected = set()
            context.user_data['selected_centers'] = selected
            
        elif data == CB_SAVE:
            # Save subscription
            user_id = update.effective_user.id
            selected_list = list(selected)
            
            self.users_collection.update_one(
                {'user_id': user_id},
                {'$set': {'subscribed_centers': selected_list}}
            )
            
            logger.info(f"User {user_id} updated subscription to {len(selected_list)} centers")
            
            # Clear user_data
            context.user_data.pop('subscription_centers', None)
            context.user_data.pop('selected_centers', None)
            
            await query.edit_message_text(self.message_service.subscription_saved(selected_list))
            return
        
        # Update the keyboard with new selection state
        keyboard = self._build_subscription_keyboard(all_centers, selected)
        text = self.message_service.subscription_prompt(len(selected), len(all_centers))
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def _status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /status command"""
        user_id = update.effective_user.id
        
        # Get user from database
        user = self.users_collection.find_one({'user_id': user_id})
        
        if not user:
            await update.message.reply_text(self.message_service.user_not_found())
        else:
            await update.message.reply_text(self.message_service.status(user))
