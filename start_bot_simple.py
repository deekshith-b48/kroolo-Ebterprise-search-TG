#!/usr/bin/env python3
"""
Simple and robust startup script for Enterprise Search Telegram Bot
"""
import sys
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import settings
from src.logging_config import setup_logging, get_logger
from src.bot import bot_application

# Set up logging
setup_logging()
logger = get_logger(__name__)

def main():
    """Start the bot with basic retry logic."""
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🚀 Starting Enterprise Search Telegram Bot (Attempt {attempt + 1}/{max_retries})")
            logger.info(f"📋 Bot Token: {settings.telegram_bot_token[:10]}...")
            logger.info(f"🔗 Backend URL: {settings.backend_base_url}")
            
            allowed_users = settings.get_allowed_user_ids()
            if allowed_users:
                logger.info(f"👥 Allowed Users: {len(allowed_users)} users")
            else:
                logger.info("👥 Access: All users allowed")
            
            # Use the synchronous method that works
            bot_application.run_polling_sync()
            
            # If we get here, the bot started successfully
            break
            
        except Exception as e:
            logger.error(f"💥 Error starting bot: {e}")
            
            if "Temporary failure in name resolution" in str(e) or "NetworkError" in str(e):
                logger.warning("🌐 Network connectivity issue detected")
                
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error("❌ Maximum retries reached. Please check your internet connection.")
                    
            elif "Unauthorized" in str(e):
                logger.error("❌ Bot token is invalid. Please check your TELEGRAM_BOT_TOKEN in .env")
                sys.exit(1)
            else:
                logger.error("❌ Unexpected error occurred")
                
            if attempt == max_retries - 1:
                raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)
