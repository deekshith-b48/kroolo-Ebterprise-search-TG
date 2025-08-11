"""
Main Telegram bot application.
"""
import asyncio
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from .config import settings
from .auth import auth_manager
from .storage import state_storage, conversation_state
from .logging_config import setup_logging, get_logger
from .handlers import (
    start_command,
    help_command,
    connect_command,
    search_command,
    upload_command,
    sources_command,
    fetch_command,
    process_command,
    status_command,
    admin_command,
    button_callback,
    handle_file_upload
)
from .handlers.messages import handle_text_message

# Set up logging
setup_logging()
logger = get_logger(__name__)


class TelegramBot:
    """Main Telegram bot class."""
    
    def __init__(self):
        self.application: Optional[Application] = None
    
    async def initialize(self):
        """Initialize the bot application."""
        
        # Create application
        self.application = (
            Application.builder()
            .token(settings.telegram_bot_token)
            .build()
        )
        
        # Store global objects in bot_data
        self.application.bot_data['auth_manager'] = auth_manager
        self.application.bot_data['state_storage'] = state_storage
        self.application.bot_data['conversation_state'] = conversation_state
        
        # Add handlers
        await self._add_handlers()
        
        # Connect to storage
        await state_storage.connect()
        
        logger.info("Bot initialized successfully")
    
    async def _add_handlers(self):
        """Add command and message handlers."""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        self.application.add_handler(CommandHandler("connect", connect_command))
        self.application.add_handler(CommandHandler("search", search_command))
        self.application.add_handler(CommandHandler("upload", upload_command))
        self.application.add_handler(CommandHandler("sources", sources_command))
        self.application.add_handler(CommandHandler("fetch", fetch_command))
        self.application.add_handler(CommandHandler("process", process_command))
        self.application.add_handler(CommandHandler("status", status_command))
        self.application.add_handler(CommandHandler("admin", admin_command))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(button_callback))
        
        # File upload handlers
        self.application.add_handler(
            MessageHandler(filters.Document.ALL, handle_file_upload)
        )
        self.application.add_handler(
            MessageHandler(filters.PHOTO, handle_file_upload)
        )
        self.application.add_handler(
            MessageHandler(filters.VOICE, handle_file_upload)
        )
        self.application.add_handler(
            MessageHandler(filters.AUDIO, handle_file_upload)
        )
        
        # Text message handler for natural language queries
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
        )
        
        # Error handler
        self.application.add_error_handler(error_handler)
        
        logger.info("Handlers added successfully")
    
    async def start_webhook(self):
        """Start bot in webhook mode."""
        if not settings.telegram_webhook_url:
            raise ValueError("TELEGRAM_WEBHOOK_URL not configured for webhook mode")
        
        await self.application.initialize()
        
        # Set webhook
        webhook_url = settings.telegram_webhook_url
        await self.application.bot.set_webhook(
            url=webhook_url,
            secret_token=settings.telegram_webhook_secret
        )
        
        logger.info("Webhook set", url=webhook_url)
        
        # Start application
        await self.application.start()
        
        logger.info("Bot started in webhook mode")
    
    async def start_polling(self):
        """Start bot in polling mode."""
        # Create application
        self.application = (
            Application.builder()
            .token(settings.telegram_bot_token)
            .build()
        )
        
        # Store global objects in bot_data
        self.application.bot_data['auth_manager'] = auth_manager
        self.application.bot_data['state_storage'] = state_storage
        self.application.bot_data['conversation_state'] = conversation_state
        
        # Add handlers
        await self._add_handlers()
        
        # Connect to storage
        await state_storage.connect()
        
        logger.info("Bot started in polling mode")
        
        # run_polling handles everything
        await self.application.run_polling()
    
    def run_polling_sync(self):
        """Start bot in polling mode (synchronous wrapper)."""
        try:
            # Create application
            self.application = (
                Application.builder()
                .token(settings.telegram_bot_token)
                .build()
            )
            
            # Store global objects in bot_data
            self.application.bot_data['auth_manager'] = auth_manager
            self.application.bot_data['state_storage'] = state_storage
            self.application.bot_data['conversation_state'] = conversation_state
            
            # Add handlers (synchronous)
            self._add_handlers_sync()
            
            logger.info("Bot started in polling mode")
            
            # Use run_polling with graceful shutdown
            self.application.run_polling(
                stop_signals=None  # Disable signal handling to avoid conflicts
            )
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
    
    def _add_handlers_sync(self):
        """Add command and message handlers (synchronous version)."""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        self.application.add_handler(CommandHandler("connect", connect_command))
        self.application.add_handler(CommandHandler("search", search_command))
        self.application.add_handler(CommandHandler("upload", upload_command))
        self.application.add_handler(CommandHandler("sources", sources_command))
        self.application.add_handler(CommandHandler("fetch", fetch_command))
        self.application.add_handler(CommandHandler("process", process_command))
        self.application.add_handler(CommandHandler("status", status_command))
        self.application.add_handler(CommandHandler("admin", admin_command))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(button_callback))
        
        # File upload handlers
        self.application.add_handler(
            MessageHandler(filters.Document.ALL, handle_file_upload)
        )
        self.application.add_handler(
            MessageHandler(filters.PHOTO, handle_file_upload)
        )
        self.application.add_handler(
            MessageHandler(filters.VOICE, handle_file_upload)
        )
        self.application.add_handler(
            MessageHandler(filters.AUDIO, handle_file_upload)
        )
        
        # Text message handler for natural language queries
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
        )
        
        # Error handler
        self.application.add_error_handler(error_handler)
        
        logger.info("Handlers added successfully")
    
    async def stop(self):
        """Stop the bot."""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        
        await state_storage.disconnect()
        
        logger.info("Bot stopped")
    
    async def process_update(self, update: Update):
        """Process a single update (for webhook mode)."""
        if self.application:
            await self.application.process_update(update)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in bot processing."""
    logger.error("Bot error", error=str(context.error), update=str(update))


# Global bot instance
bot_application = TelegramBot()
