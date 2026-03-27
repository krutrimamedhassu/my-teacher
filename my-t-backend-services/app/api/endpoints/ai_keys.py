from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List
from app.core.auth.api_key_models import (
    APIKeyCreate, APIKeyResponse, APIKeyUpdate, UsageStats, 
    UserTier, TIER_LIMITS, TIER_MESSAGES
)
from app.core.data.database import db_manager
from app.core.auth.auth_dependency import get_current_user_id
from app.logger.app_logger import app_logger

router = APIRouter()


@router.post("/create", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    request: Request
):
    """
    Create a new API key for the authenticated user.
    
    This endpoint creates a new API key that can be used to authenticate
    API requests. The key will be returned only once for security.
    """
    app_logger.log_info(f"[AIKeys] Creating API key for user with name='{key_data.name}'")
    try:
        # Get current user ID
        user_id = await get_current_user_id(request)
        app_logger.log_debug(f"[AIKeys] Creating API key for user_id={user_id}")

        # Create API key in database
        api_key_doc = db_manager.create_api_key(
            user_id=user_id,
            name=key_data.name,
            description=key_data.description
        )
        app_logger.log_info(f"[AIKeys] Successfully created API key {api_key_doc['_id']} for user {user_id}")
        
        return {
            "message": "API key created successfully",
            "api_key": api_key_doc["api_key"],  # Only returned here
            "key_info": {
                "id": api_key_doc["_id"],
                "name": api_key_doc["name"],
                "description": api_key_doc["description"],
                "key_preview": api_key_doc["key_preview"],
                "user_tier": api_key_doc["user_tier"],
                "created_at": api_key_doc["created_at"],
                "is_active": api_key_doc["is_active"]
            }
        }
        
    except ValueError as e:
        app_logger.log_warning(f"[AIKeys] API key creation validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        app_logger.log_error(f"[AIKeys] Unexpected error during API key creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during API key creation"
        )


@router.get("/", response_model=List[APIKeyResponse])
async def get_user_api_keys(request: Request):
    """
    Get all API keys for the authenticated user.
    
    This endpoint returns a list of all API keys belonging to the user,
    with sensitive information (actual keys) excluded for security.
    """
    app_logger.log_info(f"[AIKeys] Fetching API keys for user")
    try:
        # Get current user ID
        user_id = await get_current_user_id(request)
        app_logger.log_debug(f"[AIKeys] Fetching API keys for user_id={user_id}")

        # Get user's API keys
        api_keys = db_manager.get_user_api_keys(user_id)
        app_logger.log_debug(f"[AIKeys] Found {len(api_keys)} API keys for user {user_id}")
        
        # Convert to response format
        response_keys = []
        for key in api_keys:
            response_keys.append(APIKeyResponse(
                id=key["_id"],
                name=key["name"],
                description=key.get("description"),
                key_preview=key.get("key_preview", "sk-****"),
                user_id=key["user_id"],
                user_tier=UserTier(key.get("user_tier", "free")),
                created_at=key["created_at"],
                last_used=key.get("last_used"),
                is_active=key.get("is_active", True),
                usage_count=key.get("usage_count", 0),
                monthly_usage=key.get("monthly_usage", 0)
            ))
        
        app_logger.log_info(f"[AIKeys] Successfully returned {len(response_keys)} API keys")
        return response_keys

    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[AIKeys] Error fetching API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{key_id}", response_model=dict)
async def update_api_key(
    key_id: str,
    key_update: APIKeyUpdate,
    request: Request
):
    """
    Update an API key's properties.
    
    This endpoint allows updating the name, description, and active status
    of an API key owned by the authenticated user.
    """
    app_logger.log_info(f"[AIKeys] Updating API key {key_id}")
    try:
        # Get current user ID
        user_id = await get_current_user_id(request)
        app_logger.log_debug(f"[AIKeys] Updating API key {key_id} for user_id={user_id}")

        # Update API key
        update_data = {}
        if key_update.name is not None:
            update_data["name"] = key_update.name
        if key_update.description is not None:
            update_data["description"] = key_update.description
        if key_update.is_active is not None:
            update_data["is_active"] = key_update.is_active
        
        app_logger.log_debug(f"[AIKeys] Update data: {update_data}")
        success = db_manager.update_api_key(user_id, key_id, update_data)

        if not success:
            app_logger.log_warning(f"[AIKeys] API key {key_id} not found or update failed for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or update failed"
            )
        
        app_logger.log_info(f"[AIKeys] Successfully updated API key {key_id}")
        return {"message": "API key updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[AIKeys] Error updating API key {key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{key_id}", response_model=dict)
async def delete_api_key(
    key_id: str,
    request: Request
):
    """
    Delete an API key.
    
    This endpoint permanently deletes an API key owned by the authenticated user.
    The key will no longer be valid for API requests.
    """
    app_logger.log_info(f"[AIKeys] Deleting API key {key_id}")
    try:
        # Get current user ID
        user_id = await get_current_user_id(request)
        app_logger.log_debug(f"[AIKeys] Deleting API key {key_id} for user_id={user_id}")

        # Delete API key
        success = db_manager.delete_api_key(user_id, key_id)

        if not success:
            app_logger.log_warning(f"[AIKeys] API key {key_id} not found for deletion by user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        app_logger.log_info(f"[AIKeys] Successfully deleted API key {key_id}")
        return {"message": "API key deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[AIKeys] Error deleting API key {key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/usage", response_model=UsageStats)
async def get_usage_statistics(request: Request):
    """
    Get usage statistics for the authenticated user.
    
    This endpoint returns detailed usage statistics including daily and monthly
    usage counts, limits, and remaining allowances.
    """
    app_logger.log_info(f"[AIKeys] Fetching usage statistics")
    try:
        # Get current user ID
        user_id = await get_current_user_id(request)
        app_logger.log_debug(f"[AIKeys] Fetching usage stats for user_id={user_id}")

        # Get usage statistics
        stats = db_manager.get_usage_stats(user_id)

        if not stats:
            app_logger.log_debug(f"[AIKeys] No existing stats found, returning defaults for user {user_id}")
            # Return default stats for new users
            stats = {
                "daily_count": 0,
                "monthly_count": 0,
                "user_tier": "free",
                "daily_limit": TIER_LIMITS[UserTier.FREE]["daily_limit"],
                "monthly_limit": TIER_LIMITS[UserTier.FREE]["monthly_limit"],
                "daily_remaining": TIER_LIMITS[UserTier.FREE]["daily_limit"],
                "monthly_remaining": TIER_LIMITS[UserTier.FREE]["monthly_limit"]
            }
        
        app_logger.log_debug(f"[AIKeys] Returning usage stats: daily={stats.get('daily_count', 0)}, monthly={stats.get('monthly_count', 0)}")
        return UsageStats(
            user_id=user_id,
            user_tier=UserTier(stats.get("user_tier", "free")),
            total_requests=stats.get("daily_count", 0),  # This should be total, but using daily for now
            monthly_requests=stats.get("monthly_count", 0),
            daily_requests=stats.get("daily_count", 0),
            monthly_limit=stats.get("monthly_limit", -1),
            daily_limit=stats.get("daily_limit", -1),
        )
        
    except Exception as e:
        app_logger.log_error(f"[AIKeys] Error fetching usage statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/tiers", response_model=dict)
async def get_tier_information():
    """
    Get information about available user tiers and their limits.
    
    This endpoint returns information about all available user tiers,
    their limits, and upgrade paths.
    """
    app_logger.log_info(f"[AIKeys] Fetching tier information")
    try:
        tier_info = {}
        for tier in UserTier:
            limits = TIER_LIMITS[tier]
            messages = TIER_MESSAGES[tier]
            
            tier_info[tier.value] = {
                "name": tier.value.title(),
                "description": limits["description"],
                "monthly_limit": limits["monthly_limit"],
                "daily_limit": limits["daily_limit"],
                "unlimited": limits["monthly_limit"] == -1,
                "upgrade_message": messages.get("upgrade_prompt"),
                "limit_message": messages["limit_exceeded"]
            }
        
        app_logger.log_debug(f"[AIKeys] Returning information for {len(tier_info)} tiers")
        return {
            "tiers": tier_info,
            "current_limits": TIER_LIMITS
        }
        
    except Exception as e:
        app_logger.log_error(f"[AIKeys] Error fetching tier information: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )