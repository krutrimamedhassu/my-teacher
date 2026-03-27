from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any
import time

from app.logger.app_logger import app_logger

# Import logfire for optional usage
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False

router = APIRouter()


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    version: str
    timestamp: float
    uptime: float


# Store the application start time
start_time = time.time()


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the API is running correctly."
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        dict: Health status information including:
            - status: Current status of the API
            - version: API version
            - timestamp: Current server timestamp
            - uptime: Server uptime in seconds
    """
    app_logger.log_info("[HealthAPI] Starting health_check endpoint")

    # Log to Logfire if available
    if LOGFIRE_AVAILABLE:
        logfire.info('Health check requested - starting endpoint processing')

    try:
        current_time = time.time()
        uptime = current_time - start_time

        response = {
            "status": "ok",
            "version": "0.1.0",
            "timestamp": current_time,
            "uptime": uptime
        }

        # Log success to Logfire if available
        if LOGFIRE_AVAILABLE:
            logfire.info('Health check completed successfully', uptime=uptime, status="ok")

        app_logger.log_info(f"[HealthAPI] Successfully completed health_check - uptime: {uptime:.2f}s")
        return response
    except Exception as e:
        app_logger.log_error(f"[HealthAPI] Error in health_check: {str(e)}")
        raise