import logging
import asyncio
import threading
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

logger = logging.getLogger(__name__)


class BotService:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.application = None
        self.bot_thread = None
        self.loop = None
        
        # Store bot screaming status
        self.screaming = False
        
        # Pre-assign menu text
        self.FIRST_MENU = "<b>Menu 1</b>\n\nA beautiful menu with a shiny inline button."
        self.SECOND_MENU = "<b>Menu 2</b>\n\nA better menu with even more shiny inline buttons."
        
        # Pre-assign button text
        self.NEXT_BUTTON = "Next"
        self.BACK_BUTTON = "Back"
        self.TUTORIAL_BUTTON = "Tutorial"
        
        # Build keyboards
        self.FIRST_MENU_MARKUP = InlineKeyboardMarkup([[
            InlineKeyboardButton(self.NEXT_BUTTON, callback_data=self.NEXT_BUTTON)
        ]])
        self.SECOND_MENU_MARKUP = InlineKeyboardMarkup([
            [InlineKeyboardButton(self.BACK_BUTTON, callback_data=self.BACK_BUTTON)],
            [InlineKeyboardButton(self.TUTORIAL_BUTTON, url="https://core.telegram.org/bots/api")]
        ])

    def initialize(self):
        """Initialize and start the bot"""
        logger.info("Initializing Telegram bot...")
        
        # Create the Application and pass it your bot's token
        self.application = Application.builder().token(self.bot_token).build()
        
        # Register command handlers
        self.application.add_handler(CommandHandler("start", self._start))
        self.application.add_handler(CommandHandler("help", self._help))
        self.application.add_handler(CommandHandler("scream", self._scream))
        self.application.add_handler(CommandHandler("whisper", self._whisper))
        self.application.add_handler(CommandHandler("menu", self._menu))
        
        # Register handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self._button_tap))
        
        # Echo any message that is not a command
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._echo))
        
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
    
    def stop_polling(self):
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
    
    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        await update.message.reply_text(
            f'Hi {user.first_name}! Welcome to the bot.\n\n'
            'Use /help to see available commands.'
        )
    
    async def _help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        help_text = """
Available commands:
/start - Start the bot
/help - Show this help message
/scream - Enable screaming mode (messages in UPPERCASE)
/whisper - Disable screaming mode
/menu - Show interactive menu

Just send me any message and I'll echo it back!
        """
        await update.message.reply_text(help_text)
    
    async def _echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Echo the user message."""
        # Print to console
        print(f'{update.message.from_user.first_name} wrote {update.message.text}')
        
        if self.screaming and update.message.text:
            await context.bot.send_message(
                update.message.chat_id,
                update.message.text.upper(),
                # To preserve the markdown, we attach entities (bold, italic...)
                entities=update.message.entities
            )
        else:
            # This is equivalent to forwarding, without the sender's name
            await update.message.copy(update.message.chat_id)
    
    async def _scream(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Enable screaming mode."""
        self.screaming = True
        await update.message.reply_text("SCREAMING MODE ENABLED! ALL MESSAGES WILL BE IN UPPERCASE!")
    
    async def _whisper(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Disable screaming mode."""
        self.screaming = False
        await update.message.reply_text("Whisper mode enabled. Messages will be echoed normally.")
    
    async def _menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a menu with inline buttons."""
        await context.bot.send_message(
            update.message.from_user.id,
            self.FIRST_MENU,
            parse_mode=ParseMode.HTML,
            reply_markup=self.FIRST_MENU_MARKUP
        )
    
    async def _button_tap(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process the inline buttons on the menu."""
        data = update.callback_query.data
        text = ''
        markup = None
        
        if data == self.NEXT_BUTTON:
            text = self.SECOND_MENU
            markup = self.SECOND_MENU_MARKUP
        elif data == self.BACK_BUTTON:
            text = self.FIRST_MENU
            markup = self.FIRST_MENU_MARKUP
        
        # Close the query to end the client-side loading animation
        await update.callback_query.answer()
        
        # Update message content with corresponding menu section
        await update.callback_query.message.edit_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup
        )

