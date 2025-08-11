"""
Storage management for state and files.
"""
import json
import pickle
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import os
import aiofiles
import aiofiles.os
from pathlib import Path

import redis.asyncio as redis

from ..config import settings
from ..logging_config import get_logger

logger = get_logger(__name__)


class StateStorage(ABC):
    """Abstract base class for state storage."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value by key."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value with optional TTL in seconds."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a key."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass


class RedisStateStorage(StateStorage):
    """Redis-based state storage."""
    
    def __init__(self):
        self.redis_client = None
        self._connected = False
    
    async def connect(self):
        """Initialize Redis connection."""
        if not self._connected:
            self.redis_client = redis.from_url(
                settings.redis_url,
                db=settings.redis_db,
                decode_responses=True
            )
            await self.redis_client.ping()
            self._connected = True
            logger.info("Redis connection established")
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value by key."""
        await self.connect()
        try:
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error("Redis get error", key=key, error=str(e))
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value with optional TTL in seconds."""
        await self.connect()
        try:
            data = json.dumps(value, default=str)
            if ttl:
                await self.redis_client.setex(key, ttl, data)
            else:
                await self.redis_client.set(key, data)
        except Exception as e:
            logger.error("Redis set error", key=key, error=str(e))
    
    async def delete(self, key: str) -> None:
        """Delete a key."""
        await self.connect()
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error("Redis delete error", key=key, error=str(e))
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        await self.connect()
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error("Redis exists error", key=key, error=str(e))
            return False


class ConversationState:
    """Manages conversation state for users."""
    
    def __init__(self, storage: StateStorage):
        self.storage = storage
        self.default_ttl = settings.session_timeout_minutes * 60
    
    def _get_key(self, user_id: int, conversation_type: str = "main") -> str:
        """Generate Redis key for user conversation."""
        return f"conversation:{user_id}:{conversation_type}"
    
    async def get_state(self, user_id: int) -> Dict[str, Any]:
        """Get current conversation state for user."""
        key = self._get_key(user_id)
        state = await self.storage.get(key)
        return state or {}
    
    async def set_state(self, user_id: int, state: Dict[str, Any]) -> None:
        """Set conversation state for user."""
        key = self._get_key(user_id)
        state["updated_at"] = datetime.utcnow().isoformat()
        await self.storage.set(key, state, self.default_ttl)
    
    async def update_state(self, user_id: int, updates: Dict[str, Any]) -> None:
        """Update specific fields in conversation state."""
        current_state = await self.get_state(user_id)
        current_state.update(updates)
        await self.set_state(user_id, current_state)
    
    async def clear_state(self, user_id: int) -> None:
        """Clear conversation state for user."""
        key = self._get_key(user_id)
        await self.storage.delete(key)
    
    async def set_flow(self, user_id: int, flow: str, data: Dict[str, Any] = None) -> None:
        """Set current conversation flow."""
        updates = {"current_flow": flow}
        if data:
            updates["flow_data"] = data
        await self.update_state(user_id, updates)
    
    async def get_flow(self, user_id: int) -> Optional[str]:
        """Get current conversation flow."""
        state = await self.get_state(user_id)
        return state.get("current_flow")
    
    async def get_flow_data(self, user_id: int) -> Dict[str, Any]:
        """Get current flow data."""
        state = await self.get_state(user_id)
        return state.get("flow_data", {})


class FileStorage(ABC):
    """Abstract base class for file storage."""
    
    @abstractmethod
    async def upload_file(self, file_path: str, file_data: bytes, metadata: Dict[str, Any] = None) -> str:
        """Upload file and return public URL."""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage."""
        pass


class LocalFileStorage(FileStorage):
    """Local filesystem storage."""
    
    def __init__(self):
        self.storage_path = Path(settings.local_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, file_path: str, file_data: bytes, metadata: Dict[str, Any] = None) -> str:
        """Upload file to local storage."""
        full_path = self.storage_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(file_data)
        
        # Save metadata if provided
        if metadata:
            metadata_path = full_path.with_suffix(full_path.suffix + '.meta')
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(metadata, indent=2))
        
        logger.info("File uploaded to local storage", path=file_path)
        return str(full_path)
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage."""
        try:
            full_path = self.storage_path / file_path
            await aiofiles.os.remove(full_path)
            
            # Also delete metadata if exists
            metadata_path = full_path.with_suffix(full_path.suffix + '.meta')
            if await aiofiles.os.path.exists(metadata_path):
                await aiofiles.os.remove(metadata_path)
            
            logger.info("File deleted from local storage", path=file_path)
            return True
        except Exception as e:
            logger.error("Failed to delete file", path=file_path, error=str(e))
            return False


# Global storage instances
state_storage = RedisStateStorage()
conversation_state = ConversationState(state_storage)
file_storage = LocalFileStorage()
