"""
Structured Logging Middleware

This module provides comprehensive logging middleware that:
- Injects request_id, user_id, endpoint, latency
- Tracks LLM token counts
- Emits JSON logs for better observability
- Provides cost tracking capabilities
"""

import time
import uuid
import json
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.logger.app_logger import app_logger
from app.core.auth.auth_dependency import get_optional_current_user_id


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured logging with request tracing."""
    
    def __init__(self, app):
        super().__init__(app)
        self.llm_token_counts = {}  # Track LLM tokens per request
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Get user ID if authenticated
        user_id = None
        try:
            user_id = await get_optional_current_user_id(request)
        except Exception:
            pass  # User not authenticated
        
        # Log request start
        self._log_request_start(request, request_id, user_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate latency
            latency = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Get LLM token count for this request
            llm_tokens = self.llm_token_counts.get(request_id, 0)
            
            # Log request completion
            self._log_request_completion(
                request, response, request_id, user_id, latency, llm_tokens
            )
            
            return response
            
        except Exception as e:
            # Calculate latency
            latency = (time.time() - start_time) * 1000
            
            # Log request error
            self._log_request_error(
                request, request_id, user_id, latency, str(e)
            )
            raise
    
    def _log_request_start(self, request: Request, request_id: str, user_id: Optional[str]) -> None:
        """Log request start with structured data."""
        log_data = {
            "event": "request_start",
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "user_agent": request.headers.get("user-agent"),
            "client_ip": self._get_client_ip(request),
            "user_id": user_id,
            "timestamp": time.time()
        }
        
        app_logger.log_info("Request started", extra=log_data)
    
    def _log_request_completion(
        self, 
        request: Request, 
        response: Response, 
        request_id: str, 
        user_id: Optional[str], 
        latency: float,
        llm_tokens: int
    ) -> None:
        """Log request completion with structured data."""
        log_data = {
            "event": "request_complete",
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": round(latency, 2),
            "user_id": user_id,
            "llm_tokens": llm_tokens,
            "llm_cost_usd": self._calculate_llm_cost(llm_tokens),
            "timestamp": time.time()
        }
        
        # Log level based on status code
        if response.status_code >= 400:
            app_logger.log_error("Request completed with error", extra=log_data)
        else:
            app_logger.log_info("Request completed successfully", extra=log_data)
    
    def _log_request_error(
        self, 
        request: Request, 
        request_id: str, 
        user_id: Optional[str], 
        latency: float,
        error: str
    ) -> None:
        """Log request error with structured data."""
        log_data = {
            "event": "request_error",
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "latency_ms": round(latency, 2),
            "user_id": user_id,
            "error": error,
            "timestamp": time.time()
        }
        
        app_logger.log_error("Request failed", extra=log_data)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Fall back to direct IP
        return request.client.host if request.client else "unknown"
    
    def _calculate_llm_cost(self, tokens: int) -> float:
        """Calculate LLM cost in USD based on token count."""
        # Approximate cost per 1K tokens (adjust based on your LLM provider)
        cost_per_1k_tokens = 0.002  # Example: $0.002 per 1K tokens
        return round((tokens / 1000) * cost_per_1k_tokens, 4)
    
    def track_llm_tokens(self, request_id: str, tokens: int) -> None:
        """Track LLM token usage for a specific request."""
        if request_id in self.llm_token_counts:
            self.llm_token_counts[request_id] += tokens
        else:
            self.llm_token_counts[request_id] = tokens


# Global middleware instance
logging_middleware = StructuredLoggingMiddleware


def get_request_id(request: Request) -> str:
    """Get request ID from request state."""
    return getattr(request.state, 'request_id', 'unknown')


def track_llm_usage(request: Request, tokens: int) -> None:
    """Track LLM token usage for the current request."""
    request_id = get_request_id(request)
    if hasattr(request.app.state, 'logging_middleware'):
        request.app.state.logging_middleware.track_llm_tokens(request_id, tokens)


class LLMUsageTracker:
    """Context manager for tracking LLM usage."""
    
    def __init__(self, request: Request, operation: str):
        self.request = request
        self.operation = operation
        self.start_tokens = 0
        self.end_tokens = 0
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        total_tokens = self.end_tokens - self.start_tokens
        if total_tokens > 0:
            track_llm_usage(self.request, total_tokens)
            
            # Log LLM usage
            log_data = {
                "event": "llm_usage",
                "request_id": get_request_id(self.request),
                "operation": self.operation,
                "tokens_used": total_tokens,
                "cost_usd": round((total_tokens / 1000) * 0.002, 4),
                "timestamp": time.time()
            }
            app_logger.log_info("LLM usage tracked", extra=log_data)
    
    def set_start_tokens(self, tokens: int) -> None:
        """Set the starting token count."""
        self.start_tokens = tokens
    
    def set_end_tokens(self, tokens: int) -> None:
        """Set the ending token count."""
        self.end_tokens = tokens 