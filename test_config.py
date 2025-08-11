#!/usr/bin/env python3
"""
Test configuration and basic bot setup
"""
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_config():
    """Test configuration loading"""
    try:
        from src.config import settings
        print("✅ Configuration loaded successfully!")
        print(f"🤖 Bot Token: {settings.telegram_bot_token[:10]}...{settings.telegram_bot_token[-5:]}")
        print(f"🔗 Backend URL: {settings.backend_base_url}")
        print(f"👥 Allowed Users: {settings.get_allowed_user_ids()}")
        print(f"📁 Storage Type: {settings.file_storage_type}")
        print(f"🐛 Debug: {settings.debug}")
        print(f"🌐 Webhook: {settings.webhook_mode}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_token_format():
    """Test if bot token has correct format"""
    try:
        from src.config import settings
        token = settings.telegram_bot_token
        
        if not token or token == "your_telegram_bot_token_here":
            print("❌ Bot token not configured! Please set a real token in .env file")
            print("📋 Get your token from @BotFather on Telegram")
            return False
        
        if ":" not in token:
            print("❌ Invalid bot token format! Should be like: 123456789:ABC...")
            return False
            
        bot_id, bot_hash = token.split(":", 1)
        if not bot_id.isdigit():
            print("❌ Invalid bot ID in token!")
            return False
            
        if len(bot_hash) < 30:
            print("❌ Bot token hash too short!")
            return False
            
        print("✅ Bot token format looks valid!")
        return True
        
    except Exception as e:
        print(f"❌ Token validation error: {e}")
        return False

def test_simple_bot():
    """Test basic bot creation without running"""
    try:
        from src.config import settings
        from telegram.ext import Application
        
        # Just test creating the application
        application = Application.builder().token(settings.telegram_bot_token).build()
        print("✅ Bot application created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Bot creation error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Enterprise Search Bot Configuration\n")
    
    # Test configuration
    if not test_config():
        sys.exit(1)
    
    print()
    
    # Test token format
    if not test_token_format():
        print("\n💡 Fix your bot token in the .env file:")
        print("   1. Open Telegram and find @BotFather")
        print("   2. Send /newbot and follow instructions") 
        print("   3. Copy the token to TELEGRAM_BOT_TOKEN in .env")
        sys.exit(1)
    
    print()
    
    # Test bot creation
    if not test_simple_bot():
        print("\n💡 There might be a network issue or invalid token")
        sys.exit(1)
    
    print("\n🎉 All tests passed! Your bot should work.")
    print("\n🚀 To start the bot:")
    print("   python start_bot.py")
