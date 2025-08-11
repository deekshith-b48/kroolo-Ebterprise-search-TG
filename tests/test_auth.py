"""
Tests for authentication and authorization.
"""
import pytest
from unittest.mock import Mock, patch

from src.auth import AuthManager, require_auth, require_admin


def test_auth_manager_initialization():
    """Test AuthManager initialization."""
    auth = AuthManager()
    
    assert hasattr(auth, 'allowed_users')
    assert hasattr(auth, 'admin_users')
    assert hasattr(auth, 'jwt_secret')


def test_is_user_allowed():
    """Test user whitelist checking."""
    auth = AuthManager()
    auth.allowed_users = {123, 456}
    
    assert auth.is_user_allowed(123) == True
    assert auth.is_user_allowed(456) == True
    assert auth.is_user_allowed(789) == False


def test_is_user_admin():
    """Test admin privilege checking."""
    auth = AuthManager()
    auth.admin_users = {123}
    
    assert auth.is_user_admin(123) == True
    assert auth.is_user_admin(456) == False


def test_add_user():
    """Test adding user to whitelist."""
    auth = AuthManager()
    auth.allowed_users = {123}
    
    # Add new user
    result = auth.add_user(456)
    assert result == True
    assert 456 in auth.allowed_users
    
    # Try to add existing user
    result = auth.add_user(456)
    assert result == False


def test_remove_user():
    """Test removing user from whitelist."""
    auth = AuthManager()
    auth.allowed_users = {123, 456}
    auth.admin_users = {123}
    
    # Remove regular user
    result = auth.remove_user(456)
    assert result == True
    assert 456 not in auth.allowed_users
    
    # Try to remove admin user
    result = auth.remove_user(123)
    assert result == False
    assert 123 in auth.allowed_users
    
    # Try to remove non-existent user
    result = auth.remove_user(789)
    assert result == False


def test_create_backend_token():
    """Test JWT token creation."""
    auth = AuthManager()
    auth.jwt_secret = "test_secret"
    
    token = auth.create_backend_token(123)
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_backend_token():
    """Test JWT token verification."""
    auth = AuthManager()
    auth.jwt_secret = "test_secret"
    
    # Create and verify valid token
    token = auth.create_backend_token(123)
    payload = auth.verify_backend_token(token)
    
    assert payload is not None
    assert payload["sub"] == "123"
    assert payload["type"] == "bot_user"
    
    # Test invalid token
    invalid_payload = auth.verify_backend_token("invalid_token")
    assert invalid_payload is None


def test_get_auth_headers():
    """Test authentication headers generation."""
    auth = AuthManager()
    auth.jwt_secret = "test_secret"
    
    with patch('src.auth.settings') as mock_settings:
        mock_settings.backend_api_key = "test_api_key"
        
        headers = auth.get_auth_headers(123)
        
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")
        assert headers["X-Bot-User-ID"] == "123"
        assert headers["X-API-Key"] == "test_api_key"


@pytest.mark.asyncio
async def test_require_auth_decorator_authorized():
    """Test require_auth decorator with authorized user."""
    # Mock function to decorate
    mock_func = Mock(return_value="success")
    decorated_func = require_auth(mock_func)
    
    # Mock update and context
    mock_update = Mock()
    mock_update.effective_user.id = 123
    mock_context = Mock()
    mock_context.bot_data = {
        'auth_manager': Mock()
    }
    mock_context.bot_data['auth_manager'].is_user_allowed.return_value = True
    
    result = await decorated_func(mock_update, mock_context)
    
    # Verify original function was called
    mock_func.assert_called_once_with(mock_update, mock_context)


@pytest.mark.asyncio
async def test_require_auth_decorator_unauthorized():
    """Test require_auth decorator with unauthorized user."""
    # Mock function to decorate
    mock_func = Mock()
    decorated_func = require_auth(mock_func)
    
    # Mock update and context
    mock_update = Mock()
    mock_update.effective_user.id = 999
    mock_update.message.reply_text = Mock()
    mock_context = Mock()
    mock_context.bot_data = {
        'auth_manager': Mock()
    }
    mock_context.bot_data['auth_manager'].is_user_allowed.return_value = False
    
    result = await decorated_func(mock_update, mock_context)
    
    # Verify original function was NOT called
    mock_func.assert_not_called()
    
    # Verify unauthorized message was sent
    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_require_admin_decorator_admin():
    """Test require_admin decorator with admin user."""
    # Mock function to decorate
    mock_func = Mock(return_value="admin_success")
    decorated_func = require_admin(mock_func)
    
    # Mock update and context
    mock_update = Mock()
    mock_update.effective_user.id = 123
    mock_context = Mock()
    mock_context.bot_data = {
        'auth_manager': Mock()
    }
    mock_context.bot_data['auth_manager'].is_user_admin.return_value = True
    
    result = await decorated_func(mock_update, mock_context)
    
    # Verify original function was called
    mock_func.assert_called_once_with(mock_update, mock_context)


@pytest.mark.asyncio
async def test_require_admin_decorator_non_admin():
    """Test require_admin decorator with non-admin user."""
    # Mock function to decorate
    mock_func = Mock()
    decorated_func = require_admin(mock_func)
    
    # Mock update and context
    mock_update = Mock()
    mock_update.effective_user.id = 456
    mock_update.message.reply_text = Mock()
    mock_context = Mock()
    mock_context.bot_data = {
        'auth_manager': Mock()
    }
    mock_context.bot_data['auth_manager'].is_user_admin.return_value = False
    
    result = await decorated_func(mock_update, mock_context)
    
    # Verify original function was NOT called
    mock_func.assert_not_called()
    
    # Verify admin required message was sent
    mock_update.message.reply_text.assert_called_once()
