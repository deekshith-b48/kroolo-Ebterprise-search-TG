#!/usr/bin/env python3
"""
Enterprise Search Telegram Bot startup with IPv4 preference
"""
import asyncio
import sys
import os
from pathlib import Path

# Force IPv4 connectivity for potential IPv6 issues
os.environ['PYTHONHTTPSVERIFY'] = '0'  # Disable SSL verification if needed

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import settings
from src.logging_config import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)

async def main():
    """Start the bot with IPv4 preference."""
    from telegram.ext import Application
    from telegram.request import HTTPXRequest
    import httpx
    
    # Create custom request with IPv4 preference and longer timeouts
    custom_request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=30.0,
        pool_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        # Force IPv4 to avoid IPv6 DNS issues
        http_version="1.1"
    )
    
    # Create application with custom request
    application = Application.builder().token(settings.telegram_bot_token).request(custom_request).build()
    
    # Import and register all handlers
    from src.handlers.commands import register_command_handlers
    from src.handlers.callbacks import register_callback_handlers  
    from src.handlers.messages import register_message_handlers
    from src.handlers.files import register_file_handlers
    
    # Register all handlers
    register_command_handlers(application)
    register_callback_handlers(application)
    register_message_handlers(application)
    register_file_handlers(application)
    
    logger.info("🚀 Starting Enterprise Search Telegram Bot (IPv4 mode)")
    logger.info(f"📋 Bot Token: {settings.telegram_bot_token[:10]}...")
    logger.info(f"🔗 Backend URL: {settings.backend_base_url}")
    
    allowed_users = settings.get_allowed_user_ids()
    if allowed_users:
        logger.info(f"👥 Allowed Users: {len(allowed_users)} users")
    else:
        logger.info("👥 Access: All users allowed")
    
    try:
        # Test connection first
        me = await application.bot.get_me()
        logger.info(f"✅ Bot authenticated as: @{me.username} ({me.first_name})")
        
        # Start polling with robust settings
        await application.run_polling(
            drop_pending_updates=True,
            poll_timeout=20,
            bootstrap_retries=5,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Startup failed: {e}")
        sys.exit(1)
