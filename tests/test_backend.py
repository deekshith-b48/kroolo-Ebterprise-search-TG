"""
Tests for backend client.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx

from src.backend import BackendClient


@pytest.fixture
def backend_client():
    """Create backend client for testing."""
    return BackendClient()


@pytest.mark.asyncio
async def test_make_request_success(backend_client):
    """Test successful backend request."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success", "data": "test"}
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await backend_client._make_request("GET", "/test", 123)
        
        assert result == {"status": "success", "data": "test"}
        mock_client.request.assert_called_once()


@pytest.mark.asyncio
async def test_make_request_unauthorized(backend_client):
    """Test backend request with 401 response."""
    mock_response = Mock()
    mock_response.status_code = 401
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await backend_client._make_request("GET", "/test", 123)
        
        assert result == {"error": "Authentication failed"}


@pytest.mark.asyncio
async def test_make_request_timeout(backend_client):
    """Test backend request timeout."""
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.request.side_effect = httpx.TimeoutException("Timeout")
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await backend_client._make_request("GET", "/test", 123)
        
        assert result == {"error": "Request timeout"}


@pytest.mark.asyncio
async def test_connect_platform(backend_client):
    """Test platform connection."""
    with patch.object(backend_client, '_make_request') as mock_request:
        mock_request.return_value = {"status": "success", "oauth_url": "https://oauth.example.com"}
        
        result = await backend_client.connect_platform(123, "drive", {"param": "value"})
        
        mock_request.assert_called_once_with(
            "POST", "/api/connect", 123, 
            data={
                "user_id": 123,
                "platform": "drive", 
                "params": {"param": "value"}
            }
        )
        assert result["oauth_url"] == "https://oauth.example.com"


@pytest.mark.asyncio
async def test_get_sources(backend_client):
    """Test getting connected sources."""
    with patch.object(backend_client, '_make_request') as mock_request:
        mock_request.return_value = {"sources": [{"id": "source1", "name": "Test Source"}]}
        
        result = await backend_client.get_sources(123)
        
        mock_request.assert_called_once_with("GET", "/api/sources", 123)
        assert len(result["sources"]) == 1


@pytest.mark.asyncio
async def test_search(backend_client):
    """Test search functionality."""
    with patch.object(backend_client, '_make_request') as mock_request:
        mock_request.return_value = {
            "answer": "Test answer [1]",
            "citations": [{"id": 1, "title": "Test Doc"}]
        }
        
        result = await backend_client.search(123, "test query", top_k=5)
        
        mock_request.assert_called_once_with(
            "POST", "/api/search", 123,
            data={
                "user_id": 123,
                "query": "test query",
                "top_k": 5,
                "source_filters": [],
                "include_citations": True
            }
        )
        assert result["answer"] == "Test answer [1]"


@pytest.mark.asyncio
async def test_upload_file(backend_client):
    """Test file upload."""
    with patch.object(backend_client, '_make_request') as mock_request:
        mock_request.return_value = {"job_id": "job123", "document_id": "doc456"}
        
        file_data = b"test file content"
        result = await backend_client.upload_file(123, file_data, "test.txt", {"meta": "data"})
        
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0] == ("POST", "/api/upload", 123)
        assert "files" in call_args[1]


@pytest.mark.asyncio
async def test_get_job_status(backend_client):
    """Test job status checking."""
    with patch.object(backend_client, '_make_request') as mock_request:
        mock_request.return_value = {"status": "completed", "progress": 100}
        
        result = await backend_client.get_job_status(123, "job123")
        
        mock_request.assert_called_once_with(
            "GET", "/api/job-status", 123,
            params={"job_id": "job123"}
        )
        assert result["status"] == "completed"
