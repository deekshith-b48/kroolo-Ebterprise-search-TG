"""
Authentication and authorization module for the Telegram bot.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from jose import JWTError, jwt
from telegram import Update
from telegram.ext import ContextTypes

from ..config import settings
from ..logging_config import get_logger

logger = get_logger(__name__)


class AuthManager:
    """Handles user authentication and authorization."""
    
    def __init__(self):
        self.jwt_secret = settings.backend_jwt_secret
        self.allowed_users = set(settings.get_allowed_user_ids())
        self.admin_users = set(settings.get_admin_user_ids())
        # If no allowed users specified, allow all users
        self.allow_all_users = len(self.allowed_users) == 0
    
    def is_user_allowed(self, user_id: int) -> bool:
        """Check if user is in the whitelist or if all users are allowed."""
        if self.allow_all_users:
            return True
        return user_id in self.allowed_users
    
    def is_user_admin(self, user_id: int) -> bool:
        """Check if user has admin privileges."""
        return user_id in self.admin_users
    
    def add_user(self, user_id: int) -> bool:
        """Add user to allowed list (admin only)."""
        if user_id not in self.allowed_users:
            self.allowed_users.add(user_id)
            logger.info("User added to whitelist", user_id=user_id)
            return True
        return False
    
    def remove_user(self, user_id: int) -> bool:
        """Remove user from allowed list (admin only)."""
        if user_id in self.allowed_users and user_id not in self.admin_users:
            self.allowed_users.remove(user_id)
            logger.info("User removed from whitelist", user_id=user_id)
            return True
        return False
    
    def create_backend_token(self, user_id: int, expires_minutes: int = 60) -> str:
        """Create a JWT token for backend authentication."""
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "bot_user"
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def verify_backend_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a JWT token and return payload if valid."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except JWTError as e:
            logger.warning("Token verification failed", error=str(e))
            return None
    
    def get_auth_headers(self, user_id: int) -> Dict[str, str]:
        """Get authentication headers for backend requests."""
        token = self.create_backend_token(user_id)
        return {
            "Authorization": f"Bearer {token}",
            "X-Bot-User-ID": str(user_id),
            "X-API-Key": settings.backend_api_key
        }


def require_auth(func):
    """Decorator to require user authentication."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        auth_manager = context.bot_data.get('auth_manager')
        
        if not auth_manager or not auth_manager.is_user_allowed(user_id):
            await update.message.reply_text(
                "🚫 Unauthorized access. Please contact an administrator to request access.\n\n"
                f"Your Telegram ID: `{user_id}`",
                parse_mode="Markdown"
            )
            logger.warning("Unauthorized access attempt", user_id=user_id)
            return
        
        return await func(update, context)
    return wrapper


def require_admin(func):
    """Decorator to require admin privileges."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        auth_manager = context.bot_data.get('auth_manager')
        
        if not auth_manager or not auth_manager.is_user_admin(user_id):
            await update.message.reply_text(
                "🚫 Admin privileges required for this command."
            )
            logger.warning("Non-admin attempted admin command", user_id=user_id)
            return
        
        return await func(update, context)
    return wrapper


# Global auth manager instance
auth_manager = AuthManager()
