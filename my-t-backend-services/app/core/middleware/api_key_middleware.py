from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any, Tuple
import uuid
from datetime import datetime

# Dynamic import to avoid circular import
from app.core.auth.api_key_models import UserTier, TIER_MESSAGES
from app.logger.app_logger import app_logger

security = HTTPBearer(auto_error=False)


class APIKeyAuth:
    """API Key authentication and usage tracking."""
    
    def __init__(self):
        app_logger.log_info(f"[APIKeyMiddleware] Initializing APIKeyAuth")
        self.unauth_sessions = {}  # In-memory storage for unauthenticated sessions
        app_logger.log_debug(f"[APIKeyMiddleware] APIKeyAuth initialized")
    
    UNAUTH_MONTHLY_LIMIT = 10

    def get_identifier(self, request: Request) -> str:
        """Get a stable identifier for unauthenticated users based on IP address."""
        # Respect X-Forwarded-For for users behind proxies/load balancers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        return f"ip:{ip}"

    def track_unauth_usage(self, identifier: str) -> Dict[str, Any]:
        """Track monthly usage for unauthenticated users by IP."""
        now = datetime.utcnow()
        current_month = now.strftime("%Y-%m")

        if identifier not in self.unauth_sessions:
            self.unauth_sessions[identifier] = {
                "count": 0,
                "month": current_month,
                "first_request": now,
                "last_request": now,
            }

        session_data = self.unauth_sessions[identifier]

        # Reset count on new month
        if session_data["month"] != current_month:
            session_data["count"] = 0
            session_data["month"] = current_month
            session_data["first_request"] = now

        session_data["count"] += 1
        session_data["last_request"] = now

        # Clean up entries not seen in over 35 days
        expired = [
            sid for sid, data in self.unauth_sessions.items()
            if (now - data["last_request"]).total_seconds() > 35 * 86400
        ]
        for sid in expired:
            del self.unauth_sessions[sid]

        return session_data
    
    async def authenticate_request(
        self, 
        request: Request, 
        endpoint: str,
        require_auth: bool = False
    ) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
        """
        Authenticate request and track usage.
        
        Args:
            request: FastAPI request object
            endpoint: Name of the endpoint being accessed
            require_auth: Whether authentication is required
            
        Returns:
            Tuple of (api_key, user_id, usage_info)
        """
        client_ip = request.client.host if request.client else "unknown"
        app_logger.log_debug(f"[APIKeyMiddleware] Authenticating request for endpoint: {endpoint}, client: {client_ip}")

        try:
            # Try to get API key from Authorization header
            auth_header = request.headers.get("Authorization")
            api_key = None

            if auth_header and auth_header.startswith("Bearer "):
                api_key = auth_header.split(" ")[1]
                api_key_preview = f"{api_key[:8]}..." if len(api_key) > 8 else "[short_key]"
                app_logger.log_debug(f"[APIKeyMiddleware] Found API key: {api_key_preview}")
            
            # Handle authenticated requests
            if api_key:
                app_logger.log_debug(f"[APIKeyMiddleware] Authenticating API key for endpoint: {endpoint}")
                from app.core.data.database import db_manager
                api_key_doc = db_manager.authenticate_api_key(api_key)
                if not api_key_doc:
                    app_logger.log_warning(f"[APIKeyMiddleware] Invalid API key attempted: {api_key_preview}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid API key",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                
                user_id = api_key_doc["user_id"]
                app_logger.log_debug(f"[APIKeyMiddleware] API key authenticated for user: {user_id}")

                # Track usage for authenticated user
                app_logger.log_debug(f"[APIKeyMiddleware] Tracking API usage for user: {user_id}, endpoint: {endpoint}")
                usage_result = db_manager.track_api_usage(api_key, user_id, endpoint)
                
                if not usage_result.get("allowed", False):
                    reason = usage_result.get("reason", "unknown")
                    tier = usage_result.get("tier", "free")
                    app_logger.log_warning(f"[APIKeyMiddleware] Usage limit exceeded for user {user_id} - reason: {reason}, tier: {tier}")
                    
                    if reason in ["daily_limit", "monthly_limit"]:
                        limit_type = "daily" if reason == "daily_limit" else "monthly"
                        tier_enum = UserTier(tier)
                        message = TIER_MESSAGES[tier_enum]["limit_exceeded"]
                        upgrade_msg = TIER_MESSAGES[tier_enum]["upgrade_prompt"]
                        
                        detail = {
                            "error": "usage_limit_exceeded",
                            "message": message,
                            "limit_type": limit_type,
                            "user_tier": tier,
                            "upgrade_message": upgrade_msg
                        }
                        
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=detail
                        )
                
                app_logger.log_debug(f"[APIKeyMiddleware] API key authentication successful for user: {user_id}")
                return api_key, user_id, usage_result
            
            # Handle unauthenticated requests
            app_logger.log_debug(f"[APIKeyMiddleware] No API key provided, handling as unauthenticated request")
            if require_auth:
                app_logger.log_warning(f"[APIKeyMiddleware] Authentication required but not provided for endpoint: {endpoint}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Track usage for unauthenticated users
            app_logger.log_debug(f"[APIKeyMiddleware] Processing unauthenticated request for endpoint: {endpoint}")
            identifier = self.get_identifier(request)
            session_data = self.track_unauth_usage(identifier)

            # Check unauth monthly limit (10 requests)
            if session_data["count"] > self.UNAUTH_MONTHLY_LIMIT:
                app_logger.log_warning(f"[APIKeyMiddleware] Unauthenticated monthly limit exceeded for {identifier}: {session_data['count']}/{self.UNAUTH_MONTHLY_LIMIT}")
                message = TIER_MESSAGES[UserTier.UNAUTH]["limit_exceeded"]
                upgrade_msg = TIER_MESSAGES[UserTier.UNAUTH]["upgrade_prompt"]

                detail = {
                    "error": "usage_limit_exceeded",
                    "message": message,
                    "current_usage": session_data["count"],
                    "limit": self.UNAUTH_MONTHLY_LIMIT,
                    "user_tier": "unauth",
                    "upgrade_message": upgrade_msg,
                    "remaining_requests": 0
                }

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=detail
                )

            remaining = self.UNAUTH_MONTHLY_LIMIT - session_data["count"]
            usage_info = {
                "allowed": True,
                "session_id": identifier,
                "usage_count": session_data["count"],
                "remaining": remaining,
                "tier": "unauth"
            }

            app_logger.log_debug(f"[APIKeyMiddleware] Unauthenticated request successful - identifier: {identifier}, usage: {session_data['count']}/{self.UNAUTH_MONTHLY_LIMIT}")
            return None, identifier, usage_info
            
        except HTTPException:
            raise
        except Exception as e:
            app_logger.log_error(f"[APIKeyMiddleware] Error in API key authentication for endpoint {endpoint}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error"
            )


# Global instance
api_key_auth = APIKeyAuth()


async def require_api_key(request: Request, endpoint: str = "unknown") -> Tuple[str, str]:
    """
    Dependency to require valid API key.
    
    Returns:
        Tuple of (api_key, user_id)
    """
    api_key, user_id, _ = await api_key_auth.authenticate_request(
        request, endpoint, require_auth=True
    )
    return api_key, user_id


async def optional_api_key(request: Request, endpoint: str = "unknown") -> Tuple[Optional[str], str, Dict[str, Any]]:
    """
    Dependency for optional API key authentication.
    
    Returns:
        Tuple of (api_key, user_id_or_session_id, usage_info)
    """
    return await api_key_auth.authenticate_request(request, endpoint, require_auth=False)


def create_usage_response_headers(usage_info: Dict[str, Any]) -> Dict[str, str]:
    """Create response headers with usage information."""
    headers = {}
    
    if usage_info.get("tier") == "unauth":
        headers["X-RateLimit-Remaining"] = str(usage_info.get("remaining", 0))
        headers["X-RateLimit-Limit"] = "5"
        headers["X-RateLimit-Reset"] = "86400"  # 24 hours in seconds
        headers["X-Session-Id"] = usage_info.get("session_id", "")
    else:
        # For authenticated users
        limits = usage_info.get("limits", {})
        headers["X-RateLimit-Daily-Limit"] = str(limits.get("daily_limit", -1))
        headers["X-RateLimit-Monthly-Limit"] = str(limits.get("monthly_limit", -1))
        headers["X-User-Tier"] = usage_info.get("tier", "free")
    
    return headers