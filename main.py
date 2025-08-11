"""
Main entry point for the Enterprise Search Telegram Bot.
"""
import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings
from src.logging_config import setup_logging, get_logger
from src.bot import bot_application
from src.server import run_server

# Set up logging
setup_logging()
logger = get_logger(__name__)


async def main():
    """Main application entry point."""
    
    logger.info("Starting Enterprise Search Telegram Bot")
    logger.info("Configuration loaded", webhook_mode=settings.webhook_mode)
    
    try:
        # Initialize bot
        await bot_application.initialize()
        
        if settings.webhook_mode:
            logger.info("Starting in webhook mode")
            
            # Start webhook mode
            await bot_application.start_webhook()
            
            # Run web server for webhooks
            logger.info("Starting web server for webhooks")
            run_server()
            
        else:
            logger.info("Starting in polling mode")
            
            # Start polling mode
            await bot_application.start_polling()
    
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    
    except Exception as e:
        logger.error("Application error", error=str(e))
        sys.exit(1)
    
    finally:
        logger.info("Shutting down bot")
        await bot_application.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Fatal error", error=str(e))
        sys.exit(1)
