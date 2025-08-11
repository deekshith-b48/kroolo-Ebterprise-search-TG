"""
Web server for webhook handling and admin endpoints.
"""
from typing import Dict, Any
import json

from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn

from .config import settings
from .auth import auth_manager
from .logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Enterprise Search Telegram Bot API",
    description="Webhook and admin endpoints for the Telegram bot",
    version="1.0.0"
)

security = HTTPBearer()


class WebhookUpdate(BaseModel):
    """Telegram webhook update model."""
    update_id: int
    message: Dict[str, Any] = None
    callback_query: Dict[str, Any] = None


class JobCallback(BaseModel):
    """Backend job completion callback model."""
    job_id: str
    status: str
    result: Dict[str, Any] = None
    error: str = None


async def verify_webhook_secret(request: Request) -> bool:
    """Verify webhook secret token."""
    if not settings.telegram_webhook_secret:
        return True  # No secret configured
    
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    return secret_header == settings.telegram_webhook_secret


async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify admin authentication token."""
    token = credentials.credentials
    payload = auth_manager.verify_backend_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = int(payload.get("sub", 0))
    if not auth_manager.is_user_admin(user_id):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    return True


@app.post("/telegram/webhook")
async def telegram_webhook(
    update_data: WebhookUpdate,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Handle Telegram webhook updates."""
    
    # Verify webhook secret
    if not await verify_webhook_secret(request):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    logger.info("Webhook received", update_id=update_data.update_id)
    
    # Process update in background
    background_tasks.add_task(process_telegram_update, update_data.dict())
    
    return {"status": "ok"}


async def process_telegram_update(update_data: Dict[str, Any]) -> None:
    """Process Telegram update asynchronously."""
    try:
        # Import here to avoid circular imports
        from .bot import bot_application
        
        # Convert dict back to Update object and process
        from telegram import Update
        update = Update.de_json(update_data, bot_application.bot)
        
        if update:
            await bot_application.process_update(update)
        
    except Exception as e:
        logger.error("Error processing update", error=str(e), update_data=update_data)


@app.post("/api/job-callback")
async def job_callback(callback_data: JobCallback, background_tasks: BackgroundTasks):
    """Handle job completion callbacks from backend."""
    
    logger.info("Job callback received", job_id=callback_data.job_id, status=callback_data.status)
    
    # Process callback in background
    background_tasks.add_task(process_job_callback, callback_data.dict())
    
    return {"status": "received"}


async def process_job_callback(callback_data: Dict[str, Any]) -> None:
    """Process job completion callback."""
    try:
        from .storage import conversation_state
        from .bot import bot_application
        
        job_id = callback_data["job_id"]
        status = callback_data["status"]
        result = callback_data.get("result", {})
        error = callback_data.get("error")
        
        # Find users waiting for this job
        # This is a simplified approach - in production you'd store job->user mappings
        # For now, we'll broadcast to all active users (not ideal but functional)
        
        if status == "completed":
            message = f"✅ **Job Completed**\n\nJob ID: `{job_id}`\n"
            if result:
                message += f"Result: Processing successful!"
        elif status == "failed":
            message = f"❌ **Job Failed**\n\nJob ID: `{job_id}`\n"
            if error:
                message += f"Error: {error}"
        else:
            message = f"ℹ️ **Job Status Update**\n\nJob ID: `{job_id}`\nStatus: {status}"
        
        # In a real implementation, you would:
        # 1. Store job_id -> user_id mappings in Redis
        # 2. Look up the user who initiated the job
        # 3. Send notification only to that user
        
        logger.info("Job callback processed", job_id=job_id, status=status)
        
    except Exception as e:
        logger.error("Error processing job callback", error=str(e), callback_data=callback_data)


@app.get("/admin/stats")
async def get_stats(authorized: bool = Depends(verify_admin_token)):
    """Get system statistics."""
    
    # This would typically fetch real stats from storage/backend
    stats = {
        "users": {
            "total_authorized": len(auth_manager.allowed_users),
            "total_admins": len(auth_manager.admin_users),
            "active_24h": 5  # Mock data
        },
        "system": {
            "uptime": "2 days, 3 hours",
            "backend_status": "online",
            "redis_status": "online"
        },
        "usage": {
            "total_searches": 1247,
            "total_uploads": 89,
            "total_connections": 23
        }
    }
    
    return stats


@app.get("/admin/users")
async def get_users(authorized: bool = Depends(verify_admin_token)):
    """Get list of authorized users."""
    
    users = []
    for user_id in auth_manager.allowed_users:
        users.append({
            "user_id": user_id,
            "is_admin": user_id in auth_manager.admin_users,
            "last_active": "2024-01-01T00:00:00Z"  # Mock data
        })
    
    return {"users": users}


@app.post("/admin/users/{user_id}")
async def add_user(user_id: int, authorized: bool = Depends(verify_admin_token)):
    """Add user to whitelist."""
    
    success = auth_manager.add_user(user_id)
    
    return {
        "success": success,
        "message": f"User {user_id} {'added' if success else 'already exists'}"
    }


@app.delete("/admin/users/{user_id}")
async def remove_user(user_id: int, authorized: bool = Depends(verify_admin_token)):
    """Remove user from whitelist."""
    
    success = auth_manager.remove_user(user_id)
    
    return {
        "success": success,
        "message": f"User {user_id} {'removed' if success else 'not found or admin'}"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "webhook_mode": settings.webhook_mode
    }


def run_server():
    """Run the FastAPI server."""
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
