import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException, status, Response
from app.core.config import settings
from app.logger.app_logger import app_logger

# JWT settings
SECRET_KEY = "your-secret-key-here-change-in-production"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours for logged-in users
REFRESH_TOKEN_EXPIRE_DAYS = 7     # Longer-lived refresh token


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    user_id = data.get('sub', 'unknown')
    app_logger.log_info(f"[AuthenticationUtils] Entering create_access_token for user: {user_id}")
    app_logger.log_debug(f"[AuthenticationUtils] Token data keys: {list(data.keys())}, expires_delta: {expires_delta}")

    try:
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
            app_logger.log_debug(f"[AuthenticationUtils] Using custom expiration delta: {expires_delta}")
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            app_logger.log_debug(f"[AuthenticationUtils] Using default expiration: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes")

        to_encode.update({"exp": expire, "type": "access"})
        app_logger.log_debug(f"[AuthenticationUtils] Token payload prepared, expiration: {expire}")

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        app_logger.log_info(f"[AuthenticationUtils] Access token created successfully for user: {user_id}")
        return encoded_jwt

    except Exception as e:
        app_logger.log_error(f"[AuthenticationUtils] Error creating access token for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token"
        )


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT refresh token
    """
    user_id = data.get('sub', 'unknown')
    app_logger.log_info(f"[AuthenticationUtils] Entering create_refresh_token for user: {user_id}")
    app_logger.log_debug(f"[AuthenticationUtils] Token data keys: {list(data.keys())}, expires_delta: {expires_delta}")

    try:
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
            app_logger.log_debug(f"[AuthenticationUtils] Using custom expiration delta: {expires_delta}")
        else:
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            app_logger.log_debug(f"[AuthenticationUtils] Using default expiration: {REFRESH_TOKEN_EXPIRE_DAYS} days")

        to_encode.update({"exp": expire, "type": "refresh"})
        app_logger.log_debug(f"[AuthenticationUtils] Refresh token payload prepared, expiration: {expire}")

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        app_logger.log_info(f"[AuthenticationUtils] Refresh token created successfully for user: {user_id}")
        return encoded_jwt

    except Exception as e:
        app_logger.log_error(f"[AuthenticationUtils] Error creating refresh token for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create refresh token"
        )


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify
        token_type: Type of token to verify ("access" or "refresh")

    Returns:
        Decoded token data or None if invalid
    """
    # Sanitize token for logging (show only first/last few characters)
    token_preview = f"{token[:8]}...{token[-8:]}" if len(token) > 16 else "[short_token]"
    app_logger.log_info(f"[AuthenticationUtils] Entering verify_token for token: {token_preview}, type: {token_type}")

    try:
        app_logger.log_debug(f"[AuthenticationUtils] Decoding JWT token with algorithm: {ALGORITHM}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id: str = payload.get("sub")
        token_type_check: str = payload.get("type")
        exp = payload.get("exp")

        app_logger.log_debug(f"[AuthenticationUtils] Token payload extracted - user: {user_id}, type: {token_type_check}, exp: {exp}")

        if user_id is None:
            app_logger.log_warning(f"[AuthenticationUtils] Token verification failed: missing user ID in payload")
            return None

        if token_type_check != token_type:
            app_logger.log_warning(f"[AuthenticationUtils] Token verification failed: wrong token type. Expected {token_type}, got {token_type_check}")
            return None

        app_logger.log_info(f"[AuthenticationUtils] Token verified successfully for user: {user_id}, type: {token_type}")
        return payload

    except jwt.ExpiredSignatureError:
        app_logger.log_warning(f"[AuthenticationUtils] Token verification failed: token expired for token: {token_preview}")
        return None
    except jwt.JWTError as e:
        app_logger.log_warning(f"[AuthenticationUtils] Token verification failed for token {token_preview}: {str(e)}")
        return None
    except Exception as e:
        app_logger.log_error(f"[AuthenticationUtils] Unexpected error during token verification for token {token_preview}: {str(e)}")
        return None


def get_current_user_id(token: str) -> str:
    """
    Get current user ID from token.

    Args:
        token: JWT token

    Returns:
        User ID

    Raises:
        HTTPException: If token is invalid
    """
    token_preview = f"{token[:8]}...{token[-8:]}" if len(token) > 16 else "[short_token]"
    app_logger.log_info(f"[AuthenticationUtils] Entering get_current_user_id for token: {token_preview}")

    try:
        payload = verify_token(token, "access")

        if payload is None:
            app_logger.log_warning(f"[AuthenticationUtils] Token validation failed for token: {token_preview}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id: str = payload.get("sub")
        if user_id is None:
            app_logger.log_warning(f"[AuthenticationUtils] User ID missing from token payload: {token_preview}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        app_logger.log_info(f"[AuthenticationUtils] Successfully extracted user ID: {user_id} from token")
        return user_id

    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        app_logger.log_error(f"[AuthenticationUtils] Unexpected error in get_current_user_id for token {token_preview}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_user_tokens(user_id: str, email: str) -> Tuple[str, str]:
    """
    Generate both access and refresh tokens for a specific user.

    Args:
        user_id: User ID
        email: User email

    Returns:
        Tuple of (access_token, refresh_token)
    """
    app_logger.log_info(f"[AuthenticationUtils] Entering generate_user_tokens for user: {user_id}, email: {email}")

    try:
        access_data = {
            "sub": user_id,
            "email": email,
        }

        refresh_data = {
            "sub": user_id,
            "email": email,
        }

        app_logger.log_debug(f"[AuthenticationUtils] Generating access token for user: {user_id}")
        access_token = create_access_token(data=access_data)

        app_logger.log_debug(f"[AuthenticationUtils] Generating refresh token for user: {user_id}")
        refresh_token = create_refresh_token(data=refresh_data)

        app_logger.log_info(f"[AuthenticationUtils] Successfully generated both tokens for user: {user_id}")
        return access_token, refresh_token

    except Exception as e:
        app_logger.log_error(f"[AuthenticationUtils] Error generating tokens for user {user_id}: {str(e)}")
        raise




def refresh_access_token(refresh_token: str) -> Optional[str]:
    """
    Refresh an access token using a refresh token.

    Args:
        refresh_token: JWT refresh token

    Returns:
        New access token or None if refresh failed
    """
    token_preview = f"{refresh_token[:8]}...{refresh_token[-8:]}" if len(refresh_token) > 16 else "[short_token]"
    app_logger.log_info(f"[AuthenticationUtils] Entering refresh_access_token for token: {token_preview}")

    try:
        app_logger.log_debug(f"[AuthenticationUtils] Verifying refresh token: {token_preview}")
        payload = verify_token(refresh_token, "refresh")

        if payload is None:
            app_logger.log_warning(f"[AuthenticationUtils] Refresh token verification failed for token: {token_preview}")
            return None

        user_id = payload.get("sub")
        email = payload.get("email")

        app_logger.log_debug(f"[AuthenticationUtils] Extracted user data from refresh token - user: {user_id}, email: {email}")

        if user_id and email:
            access_data = {
                "sub": user_id,
                "email": email,
            }
            app_logger.log_debug(f"[AuthenticationUtils] Creating new access token for user: {user_id}")
            new_access_token = create_access_token(data=access_data)
            app_logger.log_info(f"[AuthenticationUtils] Successfully refreshed access token for user: {user_id}")
            return new_access_token
        else:
            app_logger.log_warning(f"[AuthenticationUtils] Missing user_id or email in refresh token payload. user_id: {user_id}, email: {email}")

        return None

    except Exception as e:
        app_logger.log_error(f"[AuthenticationUtils] Error refreshing access token for token {token_preview}: {str(e)}")
        return None 