"""
Test configuration and fixtures.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.config import settings
from src.auth import AuthManager
from src.storage import ConversationState, RedisStateStorage
from src.backend import BackendClient


@pytest.fixture
def mock_auth_manager():
    """Mock authentication manager."""
    auth = AuthManager()
    auth.allowed_users = {123456789, 987654321}
    auth.admin_users = {123456789}
    return auth


@pytest.fixture
def mock_storage():
    """Mock state storage."""
    storage = Mock(spec=RedisStateStorage)
    storage.get = AsyncMock(return_value=None)
    storage.set = AsyncMock()
    storage.delete = AsyncMock()
    storage.exists = AsyncMock(return_value=False)
    return storage


@pytest.fixture
def mock_conversation_state(mock_storage):
    """Mock conversation state manager."""
    return ConversationState(mock_storage)


@pytest.fixture
def mock_backend_client():
    """Mock backend client."""
    client = Mock(spec=BackendClient)
    
    # Mock search response
    client.search = AsyncMock(return_value={
        "answer": "Test answer with citations [1][2]",
        "citations": [
            {"id": 1, "title": "Test Doc 1", "url": "https://example.com/1", "snippet": "Test snippet 1"},
            {"id": 2, "title": "Test Doc 2", "url": "https://example.com/2", "snippet": "Test snippet 2"}
        ]
    })
    
    # Mock other methods
    client.connect_platform = AsyncMock(return_value={"status": "success", "oauth_url": "https://oauth.example.com"})
    client.get_sources = AsyncMock(return_value={"sources": [{"id": "test_source", "name": "Test Source"}]})
    client.upload_file = AsyncMock(return_value={"job_id": "test_job_123", "document_id": "doc_456"})
    
    return client


@pytest.fixture
def mock_update():
    """Mock Telegram Update object."""
    update = Mock()
    update.effective_user.id = 123456789
    update.effective_user.first_name = "Test"
    update.effective_chat.id = 123456789
    update.message.reply_text = AsyncMock()
    update.message.text = "/test"
    update.callback_query = None
    return update


@pytest.fixture
def mock_context():
    """Mock Telegram Context object."""
    context = Mock()
    context.args = []
    context.bot_data = {}
    context.bot.send_chat_action = AsyncMock()
    context.bot.send_message = AsyncMock()
    return context


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
