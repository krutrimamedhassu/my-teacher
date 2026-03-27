from fastapi import Request, HTTPException, status
from typing import Optional, Dict, Any, Tuple
from app.core.middleware.api_key_middleware import api_key_auth, create_usage_response_headers
from app.core.auth.auth_dependency import get_current_user_id
from app.logger.app_logger import app_logger

# Internal bypass flag for avoiding double usage tracking
INTERNAL_CALL_HEADER = "X-Internal-Call"


async def get_user_with_usage_tracking(request: Request, endpoint: str = "unknown") -> Tuple[Optional[str], str, Dict[str, Any], Dict[str, str]]:
    """
    Get user information with usage tracking for both authenticated and unauthenticated users.

    This function handles three scenarios:
    1. API key authentication (Bearer token with sk- prefix)
    2. JWT token authentication (existing session-based auth)
    3. Unauthenticated requests (track by session)

    IMPORTANT: Skips usage tracking for internal API calls to prevent double-counting.

    Returns:
        Tuple of (user_id_or_none, identifier, usage_info, response_headers)
    """
    # Get client info for logging
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")[:100]
    auth_header = request.headers.get("Authorization", "")
    auth_type = "none"

    if auth_header.startswith("Bearer sk-"):
        auth_type = "api_key"
    elif auth_header.startswith("Bearer "):
        auth_type = "jwt"

    app_logger.log_info(f"[OptionalAuth] Entering get_user_with_usage_tracking - endpoint: {endpoint}, auth_type: {auth_type}, client_ip: {client_ip}")
    app_logger.log_debug(f"[OptionalAuth] User agent: {user_agent}")

    try:
        # Check if this is an internal API call - if so, bypass usage tracking
        internal_header = request.headers.get(INTERNAL_CALL_HEADER)
        if internal_header == "true":
            app_logger.log_info(f"[OptionalAuth] Internal call detected for endpoint: {endpoint} - bypassing usage tracking")

            # Still try to get user info but don't track usage
            try:
                app_logger.log_debug(f"[OptionalAuth] Attempting to get user ID for internal call")
                user_id = await get_current_user_id(request)
                app_logger.log_debug(f"[OptionalAuth] Internal call user ID: {user_id}")
                return user_id, user_id or "internal", {"allowed": True, "tier": "internal", "bypass": True}, {}
            except Exception as e:
                app_logger.log_debug(f"[OptionalAuth] Internal call user ID extraction failed: {str(e)}")
                return None, "internal", {"allowed": True, "tier": "internal", "bypass": True}, {}

        # First try API key authentication
        if auth_header and auth_header.startswith("Bearer sk-"):
            api_key_preview = f"{auth_header[7:15]}..." if len(auth_header) > 15 else "[short_key]"
            app_logger.log_info(f"[OptionalAuth] API key authentication attempt for endpoint: {endpoint}, key: {api_key_preview}")

            try:
                api_key, user_id, usage_info = await api_key_auth.authenticate_request(
                    request, endpoint, require_auth=False
                )
                headers = create_usage_response_headers(usage_info)

                final_identifier = user_id or usage_info.get("session_id", "unknown")
                app_logger.log_info(f"[OptionalAuth] API key authentication successful - user_id: {user_id}, identifier: {final_identifier}")
                app_logger.log_debug(f"[OptionalAuth] Usage info: allowed={usage_info.get('allowed')}, tier={usage_info.get('tier')}, remaining={usage_info.get('remaining')}")

                return user_id, final_identifier, usage_info, headers
            except Exception as e:
                app_logger.log_warning(f"[OptionalAuth] API key authentication failed for key {api_key_preview}: {str(e)}")
                raise

        # Try JWT token authentication (existing auth system)
        if auth_header.startswith("Bearer "):
            token_preview = f"{auth_header[7:15]}...{auth_header[-8:]}" if len(auth_header) > 23 else "[short_token]"
            app_logger.log_info(f"[OptionalAuth] JWT token authentication attempt for endpoint: {endpoint}, token: {token_preview}")

            try:
                user_id = await get_current_user_id(request)
                if user_id:
                    app_logger.log_debug(f"[OptionalAuth] JWT authentication successful for user: {user_id}")

                    # For JWT authenticated users, track usage with their user ID
                    usage_result = {
                        "allowed": True,
                        "tier": "free",  # Default tier for JWT users
                        "daily_count": 0,
                        "monthly_count": 0,
                        "limits": {"daily_limit": 100, "monthly_limit": 100}
                    }

                    # Track usage in database for JWT users too
                    app_logger.log_debug(f"[OptionalAuth] Tracking API usage for JWT user: {user_id}, endpoint: {endpoint}")
                    from app.core.data.database import db_manager
                    db_usage = db_manager.track_api_usage(None, user_id, endpoint)

                    if db_usage.get("allowed", True):
                        usage_result.update(db_usage)
                        app_logger.log_debug(f"[OptionalAuth] Usage tracking successful for user: {user_id}")
                    else:
                        # Handle JWT user limits exceeded
                        reason = db_usage.get("reason", "unknown")
                        tier = db_usage.get("tier", "free")
                        app_logger.log_warning(f"[OptionalAuth] Usage limit exceeded for JWT user {user_id} - reason: {reason}, tier: {tier}")

                        if reason in ["daily_limit", "monthly_limit"]:
                            from app.core.auth.api_key_models import UserTier, TIER_MESSAGES
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

                            app_logger.log_warning(f"[OptionalAuth] Raising 429 exception for JWT user {user_id}: {limit_type} limit exceeded")
                            raise HTTPException(
                                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail=detail
                            )

                    headers = create_usage_response_headers(usage_result)
                    app_logger.log_info(f"[OptionalAuth] JWT user authentication and usage tracking complete for user: {user_id}")
                    return user_id, user_id, usage_result, headers
                else:
                    app_logger.log_debug(f"[OptionalAuth] JWT token validation returned no user ID")

            except HTTPException as jwt_error:
                if jwt_error.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    app_logger.log_warning(f"[OptionalAuth] Re-raising 429 exception from JWT auth")
                    raise jwt_error
                # If JWT auth fails, continue to unauthenticated flow
                app_logger.log_debug(f"[OptionalAuth] JWT auth failed with HTTP {jwt_error.status_code}, continuing to unauthenticated flow")
                pass
            except Exception as e:
                # If JWT auth fails, continue to unauthenticated flow
                app_logger.log_debug(f"[OptionalAuth] JWT auth failed with exception: {str(e)}, continuing to unauthenticated flow")
                pass

        # Handle unauthenticated requests
        app_logger.log_info(f"[OptionalAuth] Processing unauthenticated request for endpoint: {endpoint}, client_ip: {client_ip}")
        try:
            api_key, session_id, usage_info = await api_key_auth.authenticate_request(
                request, endpoint, require_auth=False
            )
            headers = create_usage_response_headers(usage_info)

            app_logger.log_info(f"[OptionalAuth] Unauthenticated request processed - session_id: {session_id}")
            app_logger.log_debug(f"[OptionalAuth] Unauthenticated usage info: allowed={usage_info.get('allowed')}, remaining={usage_info.get('remaining')}")

            return None, session_id, usage_info, headers
        except Exception as e:
            app_logger.log_error(f"[OptionalAuth] Error processing unauthenticated request: {str(e)}")
            raise

    except HTTPException:
        app_logger.log_debug(f"[OptionalAuth] HTTPException raised, re-raising")
        raise
    except Exception as e:
        app_logger.log_error(f"[OptionalAuth] Unexpected error in get_user_with_usage_tracking for endpoint {endpoint}, client_ip {client_ip}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )


async def require_auth_with_usage_tracking(request: Request, endpoint: str = "unknown") -> Tuple[str, str, Dict[str, Any], Dict[str, str]]:
    """
    Require authentication (either API key or JWT) with usage tracking.

    Returns:
        Tuple of (user_id, identifier, usage_info, response_headers)
    """
    client_ip = request.client.host if request.client else "unknown"
    app_logger.log_info(f"[OptionalAuth] Entering require_auth_with_usage_tracking - endpoint: {endpoint}, client_ip: {client_ip}")

    try:
        user_id, identifier, usage_info, headers = await get_user_with_usage_tracking(request, endpoint)

        if not user_id:
            app_logger.log_warning(f"[OptionalAuth] Authentication required but no user_id found for endpoint: {endpoint}, client_ip: {client_ip}")
            app_logger.log_debug(f"[OptionalAuth] Identifier was: {identifier}, usage_info allowed: {usage_info.get('allowed')}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please provide an API key or login.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        app_logger.log_info(f"[OptionalAuth] Authentication successful - user_id: {user_id}, identifier: {identifier}")
        app_logger.log_debug(f"[OptionalAuth] Usage info: tier={usage_info.get('tier')}, allowed={usage_info.get('allowed')}")
        return user_id, identifier, usage_info, headers

    except HTTPException:
        app_logger.log_debug(f"[OptionalAuth] HTTPException in require_auth_with_usage_tracking, re-raising")
        raise
    except Exception as e:
        app_logger.log_error(f"[OptionalAuth] Unexpected error in require_auth_with_usage_tracking for endpoint {endpoint}, client_ip {client_ip}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )


def create_limit_exceeded_response(usage_info: Dict[str, Any]) -> Dict[str, Any]:
    """Create a standardized response for when usage limits are exceeded."""
    tier = usage_info.get("tier", "unauth")
    remaining = usage_info.get("remaining", 0)

    app_logger.log_info(f"[OptionalAuth] Creating limit exceeded response for tier: {tier}")
    app_logger.log_debug(f"[OptionalAuth] Usage info details: tier={tier}, remaining={remaining}, allowed={usage_info.get('allowed')}")

    if tier == "unauth":
        response = {
            "error": "usage_limit_exceeded",
            "message": "You've reached the 10 requests/month limit for anonymous users. Please login or create an account for more.",
            "remaining_requests": remaining,
            "total_allowed": 10,
            "user_tier": "unauth",
            "upgrade_message": "Create a free account to get 100 requests per month!",
            "action": "login_required"
        }
        app_logger.log_info(f"[OptionalAuth] Created unauthenticated limit exceeded response, remaining: {remaining}")
    else:
        response = {
            "error": "usage_limit_exceeded",
            "message": f"You've reached your {tier} tier limits.",
            "user_tier": tier,
            "upgrade_message": "Upgrade to Premium for unlimited requests!" if tier == "free" else None,
            "action": "upgrade_required" if tier == "free" else "contact_support"
        }
        app_logger.log_info(f"[OptionalAuth] Created {tier} tier limit exceeded response")

    app_logger.log_debug(f"[OptionalAuth] Limit exceeded response: {response}")
    return response