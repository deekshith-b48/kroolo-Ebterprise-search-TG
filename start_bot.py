#!/usr/bin/env python3
"""
Quick start script for Enterprise Search Telegram Bot
"""
import asyncio
import sys
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
    """Start the bot in polling mode."""
    logger.info("🚀 Starting Enterprise Search Telegram Bot")
    logger.info(f"📋 Bot Token: {settings.telegram_bot_token[:10]}...")
    logger.info(f"🔗 Backend URL: {settings.backend_base_url}")
    logger.info(f"👥 Allowed Users: {len(settings.get_allowed_user_ids())}")
    
    # Use run_polling_sync for simpler startup
    bot_application.run_polling_sync()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")