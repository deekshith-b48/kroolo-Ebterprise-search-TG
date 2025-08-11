"""
Backend client for Enterprise Search API communication.
"""
from typing import Dict, List, Any, Optional
import httpx
from urllib.parse import urljoin

from ..config import settings
from ..auth import auth_manager
from ..logging_config import get_logger

logger = get_logger(__name__)


class BackendClient:
    """HTTP client for Enterprise Search backend."""
    
    def __init__(self):
        self.base_url = settings.backend_base_url
        self.timeout = 30.0
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        user_id: int,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Make authenticated request to backend."""
        
        url = urljoin(self.base_url, endpoint)
        headers = auth_manager.get_auth_headers(user_id)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if data else None,
                    params=params,
                    files=files
                )
                
                logger.info(
                    "Backend request",
                    method=method,
                    endpoint=endpoint,
                    status=response.status_code,
                    user_id=user_id
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    logger.warning("Backend authentication failed", user_id=user_id)
                    return {"error": "Authentication failed"}
                elif response.status_code == 404:
                    logger.warning("Backend endpoint not found", endpoint=endpoint)
                    return {"error": "Endpoint not found"}
                else:
                    logger.error(
                        "Backend request failed",
                        status=response.status_code,
                        response=response.text
                    )
                    return {"error": f"Request failed with status {response.status_code}"}
                    
            except httpx.TimeoutException:
                logger.error("Backend request timeout", endpoint=endpoint)
                return {"error": "Request timeout"}
            except Exception as e:
                logger.error("Backend request exception", endpoint=endpoint, error=str(e))
                return {"error": f"Request failed: {str(e)}"}
    
    async def connect_platform(
        self,
        user_id: int,
        platform: str,
        params: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Connect to external platform."""
        data = {
            "user_id": user_id,
            "platform": platform,
            "params": params or {}
        }
        return await self._make_request("POST", "/api/connect", user_id, data=data)
    
    async def get_sources(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get list of connected sources."""
        return await self._make_request("GET", "/api/sources", user_id)
    
    async def fetch_documents(
        self,
        user_id: int,
        source_id: str,
        filters: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Fetch documents from a source."""
        params = {"source_id": source_id, "user_id": user_id}
        if filters:
            params.update(filters)
        return await self._make_request("GET", "/api/fetch", user_id, params=params)
    
    async def upload_file(
        self,
        user_id: int,
        file_data: bytes,
        filename: str,
        metadata: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Upload file for indexing."""
        files = {"file": (filename, file_data)}
        data = {
            "user_id": user_id,
            "metadata": metadata or {}
        }
        return await self._make_request("POST", "/api/upload", user_id, data=data, files=files)
    
    async def process_document(
        self,
        user_id: int,
        document_id: str,
        operations: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Process a document with specified operations."""
        data = {
            "document_id": document_id,
            "operations": operations
        }
        return await self._make_request("POST", "/api/process", user_id, data=data)
    
    async def sync_source(
        self,
        user_id: int,
        source_id: str,
        mode: str = "incremental"
    ) -> Optional[Dict[str, Any]]:
        """Sync data from a source."""
        data = {
            "source_id": source_id,
            "mode": mode
        }
        return await self._make_request("POST", "/api/sync", user_id, data=data)
    
    async def search(
        self,
        user_id: int,
        query: str,
        top_k: int = None,
        source_filters: List[str] = None,
        include_citations: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Perform search with AI-powered response."""
        data = {
            "user_id": user_id,
            "query": query,
            "top_k": top_k or settings.search_results_limit,
            "source_filters": source_filters or [],
            "include_citations": include_citations
        }
        return await self._make_request("POST", "/api/search", user_id, data=data)
    
    async def get_job_status(self, user_id: int, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a background job."""
        params = {"job_id": job_id}
        return await self._make_request("GET", "/api/job-status", user_id, params=params)
    
    async def fetch_from_source(
        self,
        user_id: int,
        source_name: str,
        sync_mode: str = "incremental"
    ) -> Optional[Dict[str, Any]]:
        """Fetch data from a specific source by name."""
        data = {
            "source_name": source_name,
            "sync_mode": sync_mode,
            "user_id": user_id
        }
        return await self._make_request("POST", "/api/fetch-source", user_id, data=data)
    
    async def process_documents(
        self,
        user_id: int,
        document_ids: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Process multiple documents or all pending documents."""
        data = {
            "user_id": user_id,
            "document_ids": document_ids or []  # Empty list means process all pending
        }
        return await self._make_request("POST", "/api/process-documents", user_id, data=data)
    
    async def get_system_status(self) -> Optional[Dict[str, Any]]:
        """Get overall system status."""
        # Use admin user for system status (first admin if available)
        admin_users = list(auth_manager.admin_users)
        user_id = admin_users[0] if admin_users else 0
        return await self._make_request("GET", "/api/system-status", user_id)
    
    async def get_user_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user-specific status information."""
        return await self._make_request("GET", "/api/user-status", user_id)
    
    async def process_document(
        self,
        user_id: int,
        document_id: str,
        operations: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Process a specific document."""
        data = {
            "document_id": document_id,
            "operations": operations or ["extract", "index", "vectorize"]
        }
        return await self._make_request("POST", "/api/process-document", user_id, data=data)


# Global backend client instance
backend_client = BackendClient()
