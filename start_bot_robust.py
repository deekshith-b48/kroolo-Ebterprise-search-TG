#!/usr/bin/env python3
"""
Robust startup script for Enterprise Search Telegram Bot with network error handling
"""
import asyncio
import sys
import time
from pathlib import Path
from telegram.error import NetworkError, TelegramError

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import settings
from src.logging_config import setup_logging, get_logger
from src.bot import bot_application

# Set up logging
setup_logging()
logger = get_logger(__name__)

async def start_bot_with_retry(max_retries=5, retry_delay=10):
    """Start the bot with retry logic for network errors."""
    
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
            
            # Initialize the bot
            await bot_application.initialize()
            
            # Test bot connection first
            try:
                me = await bot_application.application.bot.get_me()
                logger.info(f"✅ Bot authenticated as: @{me.username} ({me.first_name})")
            except Exception as e:
                logger.warning(f"⚠️ Bot authentication test failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise
            
            # Start polling
            logger.info("🔄 Starting polling...")
            await bot_application.application.run_polling(
                drop_pending_updates=True,
                poll_timeout=30,  # Longer timeout
                bootstrap_retries=3  # Retry bootstrap
            )
            
        except NetworkError as e:
            logger.error(f"🌐 Network error: {e}")
            if attempt < max_retries - 1:
                logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            else:
                logger.error("❌ Maximum retries reached. Please check your internet connection.")
                raise
                
        except TelegramError as e:
            logger.error(f"📱 Telegram API error: {e}")
            if "Unauthorized" in str(e):
                logger.error("❌ Bot token is invalid. Please check your TELEGRAM_BOT_TOKEN in .env")
                sys.exit(1)
            elif attempt < max_retries - 1:
                logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            else:
                raise
                
        except Exception as e:
            logger.error(f"� Unexpected error: {e}")
            if attempt < max_retries - 1:
                logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            else:
                raise
            
        except NetworkError as e:
            logger.error(f"🌐 Network error: {e}")
            if attempt < max_retries - 1:
                logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            else:
                logger.error("❌ Maximum retries reached. Please check your internet connection.")
                raise
                
        except TelegramError as e:
            logger.error(f"📱 Telegram API error: {e}")
            if "Unauthorized" in str(e):
                logger.error("❌ Bot token is invalid. Please check your TELEGRAM_BOT_TOKEN in .env")
                sys.exit(1)
            elif attempt < max_retries - 1:
                logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            else:
                raise
                
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
            if attempt < max_retries - 1:
                logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            else:
                raise

def main():
    """Main entry point."""
    try:
        asyncio.run(start_bot_with_retry())
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
