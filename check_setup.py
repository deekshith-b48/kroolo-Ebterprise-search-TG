#!/usr/bin/env python3
"""
Setup verification script for Enterprise Search Telegram Bot
"""
import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_environment():
    """Check environment configuration."""
    print("🔍 Checking Environment Configuration...")
    
    # Load environment from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "BACKEND_BASE_URL", 
        "BACKEND_JWT_SECRET",
        "ALLOWED_USER_IDS"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def check_dependencies():
    """Check if all dependencies are installed."""
    print("\n📦 Checking Dependencies...")
    
    required_packages = [
        "telegram", "fastapi", "redis", "httpx", 
        "pydantic", "structlog", "uvicorn"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages are installed")
        return True

def check_config():
    """Check configuration loading."""
    print("\n⚙️ Checking Configuration...")
    
    try:
        from src.config import settings
        
        print(f"✅ Bot Token: {settings.telegram_bot_token[:10]}...")
        print(f"✅ Backend URL: {settings.backend_base_url}")
        print(f"✅ Allowed Users: {len(settings.get_allowed_user_ids())} users")
        print(f"✅ Admin Users: {len(settings.get_admin_user_ids())} admins")
        print(f"✅ Redis URL: {settings.redis_url}")
        print(f"✅ Webhook Mode: {settings.webhook_mode}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def check_redis():
    """Check Redis connection."""
    print("\n🔴 Checking Redis Connection...")
    
    try:
        import redis
        from src.config import settings
        
        r = redis.from_url(settings.redis_url, decode_responses=True)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Make sure Redis is running: docker run -d -p 6379:6379 redis:alpine")
        return False

def main():
    """Run all checks."""
    print("🚀 Enterprise Search Telegram Bot - Setup Check\n")
    
    checks = [
        check_environment(),
        check_dependencies(), 
        check_config(),
        check_redis()
    ]
    
    print(f"\n📊 Results: {sum(checks)}/{len(checks)} checks passed")
    
    if all(checks):
        print("\n🎉 Setup is complete! You can start the bot with:")
        print("   python start_bot.py")
        print("   or")
        print("   python main.py")
    else:
        print("\n⚠️ Please fix the issues above before starting the bot")
        sys.exit(1)

if __name__ == "__main__":
    main()