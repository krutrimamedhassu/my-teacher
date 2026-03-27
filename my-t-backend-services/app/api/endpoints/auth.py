from fastapi import APIRouter, HTTPException, status, Depends, Header, Request, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from app.core.auth.auth_models import (
    UserCreate, UserLogin, UserUpdate, PasswordUpdate, 
    EmailUpdate, UserResponse, AuthResponse, TokenResponse, UserTierUpdate
)
from app.core.data.database import db_manager
from app.core.auth.auth_utils import generate_user_tokens, refresh_access_token, verify_token
from app.core.auth.auth_dependency import get_current_user, get_current_user_id
from app.core.auth.password_migration import get_migration_status, validate_password_security
from app.logger.app_logger import app_logger
import os
import uuid
from datetime import datetime
from app.core.middleware.input_guards import validate_upload_file
from app.core.auth.api_key_models import UserTier, TIER_LIMITS

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user account.

    This endpoint creates a new user account with the provided information.
    The password will be securely hashed and stored in the database.
    Returns access and refresh tokens in response body.
    """
    app_logger.log_info(f"[Auth] Starting user registration for email: {user_data.email}")
    app_logger.log_debug(f"[Auth] Registration data - username: {user_data.username}, full_name: {user_data.full_name}")

    try:
        # Create user in database
        app_logger.log_debug("[Auth] Creating user in database")
        user_doc = db_manager.create_user(user_data.dict())
        app_logger.log_debug(f"[Auth] User created successfully with ID: {user_doc['_id']}")

        # Generate access and refresh tokens
        app_logger.log_debug("[Auth] Generating access and refresh tokens")
        access_token, refresh_token = generate_user_tokens(user_doc["_id"], user_doc["email"])
        app_logger.log_debug("[Auth] Tokens generated successfully")

        # Create response
        user_response = UserResponse(
            id=user_doc["_id"],
            email=user_doc["email"],
            username=user_doc["username"],
            full_name=user_doc["full_name"],
            profile_image_url=user_doc.get("profile_image_url"),
            created_at=user_doc["created_at"],
            updated_at=user_doc["updated_at"]
        )

        app_logger.log_info(f"[Auth] User registration completed successfully for email: {user_data.email}")

        return {
            "message": "User registered successfully",
            "user": user_response.dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except ValueError as e:
        app_logger.log_warning(f"[Auth] Registration validation failed for email {user_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        app_logger.log_error(f"[Auth] Registration error for email {user_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )


@router.post("/login", response_model=dict)
async def login_user(user_credentials: UserLogin):
    """
    Authenticate and login a user.

    This endpoint authenticates a user with their email and password,
    and returns access and refresh tokens in response body.
    """
    app_logger.log_info(f"[Auth] Login attempt for email: {user_credentials.email}")

    try:
        # Authenticate user
        app_logger.log_debug(f"[Auth] Authenticating user: {user_credentials.email}")
        user_doc = db_manager.authenticate_user(
            user_credentials.email,
            user_credentials.password
        )

        if not user_doc:
            app_logger.log_warning(f"[Auth] Login failed - invalid credentials for email: {user_credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        app_logger.log_debug(f"[Auth] User authenticated successfully: {user_doc['_id']}")

        # Generate access and refresh tokens
        app_logger.log_debug("[Auth] Generating access and refresh tokens")
        access_token, refresh_token = generate_user_tokens(user_doc["_id"], user_doc["email"])
        app_logger.log_debug("[Auth] Tokens generated successfully")

        # Create response
        user_response = UserResponse(
            id=user_doc["_id"],
            email=user_doc["email"],
            username=user_doc["username"],
            full_name=user_doc["full_name"],
            profile_image_url=user_doc.get("profile_image_url"),
            created_at=user_doc["created_at"],
            updated_at=user_doc["updated_at"]
        )

        app_logger.log_info(f"[Auth] Login successful for email: {user_credentials.email}")

        return {
            "message": "Login successful",
            "user": user_response.dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[Auth] Login error for email {user_credentials.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(request: Request):
    """
    Get current user information.

    This endpoint returns the current user's profile information
    based on the authentication cookies.
    """
    app_logger.log_info("[Auth] Fetching current user information")

    try:
        # Get user using centralized auth dependency
        app_logger.log_debug("[Auth] Retrieving current user from request")
        user_doc = await get_current_user(request)
        app_logger.log_debug(f"[Auth] Current user retrieved: {user_doc['_id']}")

        user_response = UserResponse(
            id=user_doc["_id"],
            email=user_doc["email"],
            username=user_doc["username"],
            full_name=user_doc["full_name"],
            profile_image_url=user_doc.get("profile_image_url"),
            created_at=user_doc["created_at"],
            updated_at=user_doc["updated_at"]
        )

        app_logger.log_info(f"[Auth] Current user information retrieved successfully for: {user_doc['email']}")
        return user_response

    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[Auth] Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    request: Request
):
    """
    Update user profile information.

    This endpoint allows users to update their profile information
    such as full name and username.
    """
    app_logger.log_info("[Auth] Profile update request received")
    app_logger.log_debug(f"[Auth] Profile update data: full_name={user_update.full_name}, username={user_update.username}")

    try:
        # Get user ID using centralized auth dependency
        app_logger.log_debug("[Auth] Getting current user ID")
        user_id = await get_current_user_id(request)
        app_logger.log_debug(f"[Auth] Updating profile for user: {user_id}")

        # Prepare update data
        update_data = {}
        if user_update.full_name is not None:
            update_data["full_name"] = user_update.full_name
        if user_update.username is not None:
            update_data["username"] = user_update.username
        if user_update.profile_image_url is not None:
            update_data["profile_image_url"] = user_update.profile_image_url

        app_logger.log_debug(f"[Auth] Profile update fields: {list(update_data.keys())}")

        # Update user profile
        app_logger.log_debug("[Auth] Executing profile update in database")
        success = db_manager.update_user_profile(user_id, update_data)

        if not success:
            app_logger.log_error(f"[Auth] Profile update failed in database for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )

        # Get updated user
        app_logger.log_debug("[Auth] Fetching updated user data")
        user_doc = db_manager.get_user_by_id(user_id)

        if not user_doc:
            app_logger.log_error(f"[Auth] User not found after profile update: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_response = UserResponse(
            id=user_doc["_id"],
            email=user_doc["email"],
            username=user_doc["username"],
            full_name=user_doc["full_name"],
            profile_image_url=user_doc.get("profile_image_url"),
            created_at=user_doc["created_at"],
            updated_at=user_doc["updated_at"]
        )

        app_logger.log_info(f"[Auth] Profile updated successfully for user: {user_id}")
        return user_response

    except ValueError as e:
        app_logger.log_warning(f"[Auth] Profile update validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[Auth] Error updating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/password", response_model=dict)
async def update_password(
    password_update: PasswordUpdate,
    request: Request
):
    """
    Update user password.

    This endpoint allows users to update their password.
    The current password must be provided for verification.
    """
    app_logger.log_info("[Auth] Password update request received")

    try:
        # Get user ID using centralized auth dependency
        app_logger.log_debug("[Auth] Getting current user ID for password update")
        user_id = await get_current_user_id(request)
        app_logger.log_debug(f"[Auth] Updating password for user: {user_id}")

        # Update password
        app_logger.log_debug("[Auth] Executing password update in database")
        success = db_manager.update_user_password(
            user_id,
            password_update.current_password,
            password_update.new_password
        )

        if not success:
            app_logger.log_error(f"[Auth] Password update failed in database for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )

        app_logger.log_info(f"[Auth] Password updated successfully for user: {user_id}")
        return {"message": "Password updated successfully"}

    except ValueError as e:
        app_logger.log_warning(f"[Auth] Password update validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[Auth] Error updating password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/email", response_model=dict)
async def update_email(
    email_update: EmailUpdate,
    request: Request
):
    """
    Update user email.

    This endpoint allows users to update their email address.
    The current password must be provided for verification.
    """
    app_logger.log_info(f"[Auth] Email update request for new email: {email_update.new_email}")

    try:
        # Get user ID using centralized auth dependency
        app_logger.log_debug("[Auth] Getting current user ID for email update")
        user_id = await get_current_user_id(request)
        app_logger.log_debug(f"[Auth] Updating email for user: {user_id}")

        # Update email
        app_logger.log_debug("[Auth] Executing email update in database")
        success = db_manager.update_user_email(
            user_id,
            email_update.current_password,
            email_update.new_email
        )

        if not success:
            app_logger.log_error(f"[Auth] Email update failed in database for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update email"
            )

        app_logger.log_info(f"[Auth] Email updated successfully for user: {user_id} to {email_update.new_email}")
        return {"message": "Email updated successfully"}

    except ValueError as e:
        app_logger.log_warning(f"[Auth] Email update validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[Auth] Error updating email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )




@router.get("/migration-status", response_model=dict)
async def get_password_migration_status():
    """
    Get password migration status from SHA-256 to bcrypt.

    This endpoint provides information about the current state of password
    migration and security validation.
    """
    app_logger.log_info("[Auth] Migration status request received")

    try:
        app_logger.log_debug("[Auth] Getting migration status")
        migration_status = get_migration_status()
        app_logger.log_debug(f"[Auth] Migration status: {migration_status.get('status', 'unknown')}")

        app_logger.log_debug("[Auth] Validating password security")
        security_validation = validate_password_security()
        app_logger.log_debug(f"[Auth] Security score: {security_validation.get('security_score', 0)}")

        recommendations = _get_security_recommendations(migration_status, security_validation)
        app_logger.log_debug(f"[Auth] Generated {len(recommendations)} recommendations")

        app_logger.log_info("[Auth] Migration status retrieved successfully")

        return {
            "migration": migration_status,
            "security": security_validation,
            "recommendations": recommendations
        }

    except Exception as e:
        app_logger.log_error(f"[Auth] Error getting migration status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def _get_security_recommendations(migration_status: dict, security_validation: dict) -> list:
    """Get security recommendations based on current status."""
    app_logger.log_debug("[Auth] Generating security recommendations")
    recommendations = []

    if migration_status.get("status") == "not_started":
        recommendations.append("Start migrating passwords from SHA-256 to bcrypt")
        app_logger.log_debug("[Auth] Added recommendation: Start password migration")

    if migration_status.get("legacy_sha256_users", 0) > 0:
        recommendations.append("Legacy passwords will be migrated automatically on next login")
        app_logger.log_debug(f"[Auth] Added recommendation for {migration_status.get('legacy_sha256_users', 0)} legacy users")

    if security_validation.get("users_without_hash", 0) > 0:
        recommendations.append("Some users have no password hash - investigate immediately")
        app_logger.log_warning(f"[Auth] Security issue: {security_validation.get('users_without_hash', 0)} users without hash")

    if security_validation.get("inconsistent_users", 0) > 0:
        recommendations.append("Some migrated users still have salt fields - run cleanup")
        app_logger.log_debug(f"[Auth] Found {security_validation.get('inconsistent_users', 0)} inconsistent users")

    if security_validation.get("security_score", 0) < 100:
        recommendations.append("Not all users have secure password hashes")
        app_logger.log_debug(f"[Auth] Security score below optimal: {security_validation.get('security_score', 0)}")

    if not recommendations:
        recommendations.append("Password security is optimal")
        app_logger.log_debug("[Auth] Password security is optimal")

    app_logger.log_debug(f"[Auth] Generated {len(recommendations)} security recommendations")
    return recommendations


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token.

    This endpoint allows clients to get a new access token using a valid refresh token.
    """
    app_logger.log_info("[Auth] Token refresh request received")
    app_logger.log_debug("[Auth] Processing refresh token")

    try:
        app_logger.log_debug("[Auth] Validating refresh token and generating new access token")
        new_access_token = refresh_access_token(refresh_token)

        if not new_access_token:
            app_logger.log_warning("[Auth] Token refresh failed - invalid or expired refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        app_logger.log_info("[Auth] Token refresh successful")

        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[Auth] Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )


@router.post("/logout", response_model=dict)
async def logout_user():
    """
    Logout user.

    This endpoint simply confirms logout. Token invalidation should be handled client-side.
    """
    app_logger.log_info("[Auth] User logout request received")

    try:
        app_logger.log_debug("[Auth] Processing logout confirmation")
        app_logger.log_info("[Auth] User logout completed successfully")
        return {"message": "Logged out successfully"}

    except Exception as e:
        app_logger.log_error(f"[Auth] Error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 


@router.post("/profile-image", response_model=Dict[str, Any])
async def upload_profile_image(
    file: UploadFile = File(...),
    request: Request = None
):
    """
    Upload a profile image for the current user.

    This endpoint accepts image files (JPG, PNG, GIF, WebP) and stores them
    with a unique filename. The image URL is then updated in the user's profile.
    """
    app_logger.log_info(f"[Auth] Profile image upload request for file: {file.filename}")
    app_logger.log_debug(f"[Auth] File details - size: {file.size if hasattr(file, 'size') else 'unknown'}, content_type: {file.content_type}")

    try:
        # Get current user
        app_logger.log_debug("[Auth] Getting current user for profile image upload")
        user_doc = await get_current_user(request)
        user_id = user_doc["_id"]
        app_logger.log_debug(f"[Auth] Profile image upload for user: {user_id}")

        # Validate file upload
        app_logger.log_debug("[Auth] Validating upload file")
        validation_result = validate_upload_file(file, request, user_id)
        app_logger.log_debug("[Auth] File validation passed")

        # Check if file is an image
        if not file.content_type.startswith("image/"):
            app_logger.log_warning(f"[Auth] Invalid file type for profile image: {file.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed for profile images"
            )

        # Create uploads directory if it doesn't exist
        uploads_dir = "static/uploads/profile_images"
        app_logger.log_debug(f"[Auth] Ensuring uploads directory exists: {uploads_dir}")
        os.makedirs(uploads_dir, exist_ok=True)

        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{user_id}_{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(uploads_dir, unique_filename)
        app_logger.log_debug(f"[Auth] Generated unique filename: {unique_filename}")

        # Save the file
        app_logger.log_debug(f"[Auth] Saving file to: {file_path}")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        app_logger.log_debug(f"[Auth] File saved successfully, size: {len(content)} bytes")

        # Generate URL for the uploaded image
        image_url = f"/static/uploads/profile_images/{unique_filename}"
        app_logger.log_debug(f"[Auth] Generated image URL: {image_url}")

        # Update user profile with image URL
        app_logger.log_debug("[Auth] Updating user profile with image URL")
        update_data = {"profile_image_url": image_url}
        success = db_manager.update_user_profile(user_id, update_data)

        if not success:
            app_logger.log_error(f"[Auth] Failed to update profile with image URL for user: {user_id}")
            # Clean up the uploaded file if profile update fails
            if os.path.exists(file_path):
                os.remove(file_path)
                app_logger.log_debug("[Auth] Cleaned up uploaded file due to profile update failure")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile with image URL"
            )

        app_logger.log_info(f"[Auth] Profile image uploaded successfully for user: {user_id}")

        return {
            "message": "Profile image uploaded successfully",
            "image_url": image_url,
            "file_info": {
                "filename": unique_filename,
                "size": len(content),
                "content_type": file.content_type
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[Auth] Error uploading profile image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during profile image upload"
        ) 


@router.get("/tier", response_model=Dict[str, Any])
async def get_user_tier(request: Request):
    """
    Get the current user's subscription tier and limits.
    """
    app_logger.log_info("[Auth] User tier information request received")

    try:
        app_logger.log_debug("[Auth] Getting current user for tier information")
        user_doc = await get_current_user(request)
        user_tier_value = user_doc.get("user_tier", UserTier.FREE.value)
        app_logger.log_debug(f"[Auth] User {user_doc['_id']} has tier: {user_tier_value}")

        tier_enum = UserTier(user_tier_value)
        limits = TIER_LIMITS[tier_enum]
        app_logger.log_debug(f"[Auth] Retrieved limits for tier {tier_enum.value}: {limits}")

        app_logger.log_info(f"[Auth] User tier information retrieved successfully for user: {user_doc['_id']}")

        return {
            "user_id": user_doc["_id"],
            "tier": tier_enum.value,
            "limits": limits
        }
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[Auth] Error getting user tier: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/tier", response_model=Dict[str, Any])
async def update_user_tier(update: UserTierUpdate, request: Request):
    """
    Update the current user's subscription tier (free, premium).
    """
    app_logger.log_info(f"[Auth] User tier update request to: {update.tier.value}")

    try:
        app_logger.log_debug("[Auth] Getting current user ID for tier update")
        user_id = await get_current_user_id(request)
        app_logger.log_debug(f"[Auth] Updating tier for user: {user_id} to {update.tier.value}")

        app_logger.log_debug("[Auth] Executing tier update in database")
        success = db_manager.update_user_tier(user_id, update.tier)
        if not success:
            app_logger.log_error(f"[Auth] Failed to update user tier in database for user: {user_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update user tier")

        app_logger.log_info(f"[Auth] User tier updated successfully for user: {user_id} to {update.tier.value}")
        return {"message": "User tier updated", "tier": update.tier.value}
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[Auth] Error updating user tier: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")