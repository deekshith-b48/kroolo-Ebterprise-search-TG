"""
Configuration management for the Enterprise Search Telegram Bot.
"""
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Telegram Bot Configuration
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    telegram_webhook_url: Optional[str] = Field(None, env="TELEGRAM_WEBHOOK_URL")
    telegram_webhook_secret: Optional[str] = Field(None, env="TELEGRAM_WEBHOOK_SECRET")
    
    # Backend Configuration
    backend_base_url: str = Field(..., env="BACKEND_BASE_URL")
    backend_api_key: str = Field(..., env="BACKEND_API_KEY")
    backend_jwt_secret: str = Field(..., env="BACKEND_JWT_SECRET")
    
    # Redis Configuration
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    redis_db: int = Field(0, env="REDIS_DB")
    
    # Authentication
    allowed_user_ids: str = Field("", env="ALLOWED_USER_IDS")
    admin_user_ids: str = Field("", env="ADMIN_USER_IDS")
    
    # File Storage
    file_storage_type: str = Field("local", env="FILE_STORAGE_TYPE")
    aws_access_key_id: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    aws_bucket_name: Optional[str] = Field(None, env="AWS_BUCKET_NAME")
    aws_region: str = Field("us-east-1", env="AWS_REGION")
    local_storage_path: str = Field("./uploads", env="LOCAL_STORAGE_PATH")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    
    # Bot Settings
    max_file_size_mb: int = Field(50, env="MAX_FILE_SIZE_MB")
    session_timeout_minutes: int = Field(30, env="SESSION_TIMEOUT_MINUTES")
    search_results_limit: int = Field(10, env="SEARCH_RESULTS_LIMIT")
    pagination_size: int = Field(5, env="PAGINATION_SIZE")
    
    # Development
    debug: bool = Field(False, env="DEBUG")
    webhook_mode: bool = Field(True, env="WEBHOOK_MODE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def get_allowed_user_ids(self) -> List[int]:
        """Get the parsed allowed user IDs list."""
        if not hasattr(self, '_allowed_user_ids'):
            self._allowed_user_ids = [int(uid.strip()) for uid in self.allowed_user_ids.split(",") if uid.strip()] if self.allowed_user_ids else []
        return self._allowed_user_ids
    
    def get_admin_user_ids(self) -> List[int]:
        """Get the parsed admin user IDs list."""
        if not hasattr(self, '_admin_user_ids'):
            self._admin_user_ids = [int(uid.strip()) for uid in self.admin_user_ids.split(",") if uid.strip()] if self.admin_user_ids else []
        return self._admin_user_ids


# Global settings instance
settings = Settings()
