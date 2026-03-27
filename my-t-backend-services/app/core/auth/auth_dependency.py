"""
Centralized Authentication Dependency

This module provides a comprehensive authentication dependency that:
- Verifies JWT tokens (expiry + signature)
- Loads user from database
- Enforces user status (active/suspended)
- Can be used in routes, tool calls, and WebSockets
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security.utils import get_authorization_scheme_param
from app.core.auth.auth_utils import verify_token
from app.logger.app_logger import app_logger


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Centralized authentication dependency.

    Verifies JWT token from Authorization header, loads user from database, and enforces user status.
    Can be used in routes, tool calls, and WebSockets.

    Args:
        request: FastAPI request object

    Returns:
        User data if authenticated and active

    Raises:
        HTTPException: If authentication fails or user is suspended
    """
    app_logger.log_debug("[AuthenticationDependency] Starting user authentication process")

    try:
        # Get Authorization header
        app_logger.log_debug("[AuthenticationDependency] Extracting Authorization header")
        authorization = request.headers.get("Authorization")

        if not authorization:
            app_logger.log_warning("[AuthenticationDependency] No Authorization header found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        app_logger.log_debug("[AuthenticationDependency] Authorization header found, parsing scheme and credentials")
        scheme, credentials = get_authorization_scheme_param(authorization)

        if not authorization or scheme.lower() != "bearer":
            app_logger.log_warning(f"[AuthenticationDependency] Invalid authentication scheme: {scheme}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not credentials:
            app_logger.log_warning("[AuthenticationDependency] No credentials found in Authorization header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        app_logger.log_debug("[AuthenticationDependency] Credentials extracted, verifying token")

        # Verify access token
        payload = verify_token(credentials, "access")
        if not payload:
            app_logger.log_warning("[AuthenticationDependency] Token verification failed - invalid or expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        app_logger.log_debug("[AuthenticationDependency] Token verified successfully, extracting user ID")
        user_id = payload.get("sub")
        if not user_id:
            app_logger.log_error("[AuthenticationDependency] Token payload missing user ID (sub)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        app_logger.log_debug(f"[AuthenticationDependency] User ID extracted: {user_id}")

        # Load user from database
        app_logger.log_debug("[AuthenticationDependency] Loading user from database")
        from app.core.data.database import db_manager
        user_doc = db_manager.get_user_by_id(user_id)
        if not user_doc:
            app_logger.log_warning(f"[AuthenticationDependency] User not found in database: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        app_logger.log_debug(f"[AuthenticationDependency] User loaded from database: {user_doc['email']}")

        # Enforce user status
        app_logger.log_debug("[AuthenticationDependency] Checking user active status")
        if not user_doc.get("is_active", True):
            app_logger.log_warning(f"[AuthenticationDependency] User account suspended: {user_doc['email']}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is suspended"
            )

        app_logger.log_info(f"[AuthenticationDependency] User authenticated successfully: {user_doc['email']} (ID: {user_doc['_id']})")
        return user_doc

    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[AuthenticationDependency] Unexpected error in authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )


async def get_current_user_id(request: Request) -> str:
    """
    Get current user ID from authentication.

    Args:
        request: FastAPI request object

    Returns:
        User ID if authenticated and active

    Raises:
        HTTPException: If authentication fails or user is suspended
    """
    app_logger.log_debug("[AuthenticationDependency] Getting current user ID")
    user_doc = await get_current_user(request)
    user_id = user_doc["_id"]
    app_logger.log_debug(f"[AuthenticationDependency] User ID retrieved: {user_id}")
    return user_id


async def get_optional_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, otherwise return None.

    Args:
        request: FastAPI request object

    Returns:
        User data if authenticated and active, None otherwise
    """
    app_logger.log_debug("[AuthenticationDependency] Attempting optional user authentication")
    try:
        user_doc = await get_current_user(request)
        app_logger.log_debug(f"[AuthenticationDependency] Optional authentication successful: {user_doc['email']}")
        return user_doc
    except HTTPException as e:
        app_logger.log_debug(f"[AuthenticationDependency] Optional authentication failed (expected): {e.detail}")
        return None


async def get_optional_current_user_id(request: Request) -> Optional[str]:
    """
    Get current user ID if authenticated, otherwise return None.

    Args:
        request: FastAPI request object

    Returns:
        User ID if authenticated and active, None otherwise
    """
    app_logger.log_debug("[AuthenticationDependency] Attempting optional user ID retrieval")
    try:
        user_id = await get_current_user_id(request)
        app_logger.log_debug(f"[AuthenticationDependency] Optional user ID retrieved: {user_id}")
        return user_id
    except HTTPException as e:
        app_logger.log_debug(f"[AuthenticationDependency] Optional user ID retrieval failed (expected): {e.detail}")
        return None


def require_active_user(user_doc: Dict[str, Any]) -> None:
    """
    Check if user is active, raise exception if suspended.

    Args:
        user_doc: User document from database

    Raises:
        HTTPException: If user is suspended
    """
    app_logger.log_debug(f"[AuthenticationDependency] Checking active status for user: {user_doc.get('email', 'unknown')}")
    if not user_doc.get("is_active", True):
        app_logger.log_warning(f"[AuthenticationDependency] User account is suspended: {user_doc.get('email', 'unknown')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is suspended"
        )
    app_logger.log_debug("[AuthenticationDependency] User active status check passed")


def get_user_permissions(user_doc: Dict[str, Any]) -> Dict[str, bool]:
    """
    Get user permissions based on user data.

    Args:
        user_doc: User document from database

    Returns:
        Dictionary of permissions
    """
    app_logger.log_debug(f"[AuthenticationDependency] Getting permissions for user: {user_doc.get('email', 'unknown')}")

    # This can be extended based on your permission system
    permissions = {
        "can_upload": user_doc.get("is_active", True),
        "can_delete": user_doc.get("is_active", True),
        "can_admin": user_doc.get("is_admin", False),
        "can_export": user_doc.get("is_active", True),
    }

    app_logger.log_debug(f"[AuthenticationDependency] User permissions calculated: {permissions}")
    return permissions 