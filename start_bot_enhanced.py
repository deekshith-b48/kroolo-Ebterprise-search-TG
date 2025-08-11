#!/usr/bin/env python3
"""
Enhanced start script with better error handling and network timeouts
"""
import sys
import signal
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import settings
from src.logging_config import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\n🛑 Received shutdown signal. Stopping bot...")
    sys.exit(0)

def main():
    """Start the bot with enhanced error handling"""
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Starting Enterprise Search Telegram Bot")
    logger.info(f"📋 Bot Token: {settings.telegram_bot_token[:10]}...")
    logger.info(f"🔗 Backend URL: {settings.backend_base_url}")
    logger.info(f"👥 Allowed Users: {len(settings.get_allowed_user_ids())}")
    
    try:
        # Import here to avoid early loading issues
        from telegram.ext import Application
        from src.handlers import (
            start_command, help_command, connect_command, search_command,
            upload_command, sources_command, fetch_command, process_command,
            status_command, admin_command, button_callback, handle_file_upload
        )
        from src.handlers.messages import handle_text_message
        from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
        
        # Create application with custom settings
        application = (
            Application.builder()
            .token(settings.telegram_bot_token)
            .connect_timeout(30.0)
            .read_timeout(30.0)
            .write_timeout(30.0)
            .pool_timeout(30.0)
            .build()
        )
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("connect", connect_command))
        application.add_handler(CommandHandler("search", search_command))
        application.add_handler(CommandHandler("upload", upload_command))
        application.add_handler(CommandHandler("sources", sources_command))
        application.add_handler(CommandHandler("fetch", fetch_command))
        application.add_handler(CommandHandler("process", process_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("admin", admin_command))
        
        # Callback handler
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # File handlers
        application.add_handler(MessageHandler(filters.Document.ALL, handle_file_upload))
        application.add_handler(MessageHandler(filters.PHOTO, handle_file_upload))
        application.add_handler(MessageHandler(filters.VOICE, handle_file_upload))
        application.add_handler(MessageHandler(filters.AUDIO, handle_file_upload))
        
        # Text message handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        
        logger.info("✅ Handlers added successfully")
        logger.info("🔄 Starting bot polling...")
        
        # Run with custom settings
        application.run_polling(
            timeout=30,
            bootstrap_retries=3,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30,
            stop_signals=None
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        print(f"\n❌ Error starting bot: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your internet connection")
        print("   2. Verify your bot token with @BotFather")
        print("   3. Try running: python test_config.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
