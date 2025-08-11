#!/usr/bin/env python3
"""
Test script to verify authentication configuration
"""
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import settings
from src.auth import auth_manager

def test_auth():
    """Test the authentication configuration."""
    
    print("🔍 Authentication Configuration Test")
    print("=" * 40)
    
    # Check configuration
    allowed_users = settings.get_allowed_user_ids()
    admin_users = settings.get_admin_user_ids()
    
    print(f"📋 ALLOWED_USER_IDS from .env: '{settings.allowed_user_ids}'")
    print(f"👥 Parsed allowed users: {allowed_users}")
    print(f"👑 Admin users: {admin_users}")
    print(f"🌍 Allow all users: {auth_manager.allow_all_users}")
    print()
    
    # Test specific user
    test_user_id = 5549283167
    is_allowed = auth_manager.is_user_allowed(test_user_id)
    
    print(f"🧪 Testing user ID: {test_user_id}")
    print(f"✅ Access allowed: {is_allowed}")
    print()
    
    # Test a few more users
    test_users = [1234567, 9876543, 5549283167]
    for user_id in test_users:
        allowed = auth_manager.is_user_allowed(user_id)
        status = "✅ ALLOWED" if allowed else "❌ DENIED"
        print(f"User {user_id}: {status}")

if __name__ == "__main__":
    test_auth()
