"""
Tests for command handlers.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.handlers.commands import (
    start_command,
    help_command,
    search_command,
    format_search_response
)


@pytest.mark.asyncio
async def test_start_command(mock_update, mock_context, mock_auth_manager):
    """Test /start command."""
    with patch('src.handlers.commands.auth_manager', mock_auth_manager):
        with patch('src.handlers.commands.conversation_state') as mock_conv_state:
            mock_conv_state.clear_state = AsyncMock()
            
            await start_command(mock_update, mock_context)
            
            # Verify message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Welcome to Enterprise Search Bot" in call_args[0][0]
            
            # Verify state was cleared
            mock_conv_state.clear_state.assert_called_once_with(123456789)


@pytest.mark.asyncio
async def test_help_command(mock_update, mock_context, mock_auth_manager):
    """Test /help command."""
    with patch('src.handlers.commands.auth_manager', mock_auth_manager):
        await help_command(mock_update, mock_context)
        
        # Verify message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Enterprise Search Bot Commands" in call_args[0][0]


@pytest.mark.asyncio
async def test_search_command_no_args(mock_update, mock_context, mock_auth_manager):
    """Test /search command without arguments."""
    with patch('src.handlers.commands.auth_manager', mock_auth_manager):
        mock_context.args = []
        
        await search_command(mock_update, mock_context)
        
        # Verify usage message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Search Usage" in call_args[0][0]


@pytest.mark.asyncio
async def test_search_command_with_query(mock_update, mock_context, mock_auth_manager, mock_backend_client):
    """Test /search command with query."""
    with patch('src.handlers.commands.auth_manager', mock_auth_manager):
        with patch('src.handlers.commands.backend_client', mock_backend_client):
            mock_context.args = ["test", "query"]
            
            await search_command(mock_update, mock_context)
            
            # Verify backend was called
            mock_backend_client.search.assert_called_once_with(123456789, "test query")
            
            # Verify response was sent
            mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio 
async def test_search_command_backend_error(mock_update, mock_context, mock_auth_manager):
    """Test /search command with backend error."""
    with patch('src.handlers.commands.auth_manager', mock_auth_manager):
        with patch('src.handlers.commands.backend_client') as mock_backend:
            mock_backend.search = AsyncMock(return_value={"error": "Backend unavailable"})
            mock_context.args = ["test"]
            
            await search_command(mock_update, mock_context)
            
            # Verify error message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Search failed" in call_args[0][0]


def test_format_search_response():
    """Test search response formatting."""
    result = {
        "answer": "Test answer with citations [1][2]",
        "citations": [
            {"id": 1, "title": "Doc 1", "url": "https://example.com/1", "snippet": "Snippet 1"},
            {"id": 2, "title": "Doc 2", "url": "https://example.com/2", "snippet": "Snippet 2"}
        ]
    }
    
    response = format_search_response(result)
    
    assert "Search Results" in response
    assert "Test answer with citations [1][2]" in response
    assert "Sources:" in response
    assert "[1] [Doc 1](https://example.com/1)" in response
    assert "[2] [Doc 2](https://example.com/2)" in response


def test_format_search_response_no_citations():
    """Test search response formatting without citations."""
    result = {
        "answer": "Test answer without citations",
        "citations": []
    }
    
    response = format_search_response(result)
    
    assert "Search Results" in response
    assert "Test answer without citations" in response
    assert "Sources:" not in response


def test_format_search_response_empty():
    """Test search response formatting with empty result."""
    result = {}
    
    response = format_search_response(result)
    
    assert "No results found" in response
