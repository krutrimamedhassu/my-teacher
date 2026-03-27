from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class UserTier(str, Enum):
    """User tier enumeration."""
    UNAUTH = "unauth"
    FREE = "free" 
    PREMIUM = "premium"


class APIKeyBase(BaseModel):
    """Base API key model."""
    name: str = Field(..., min_length=1, max_length=100, description="Name for the API key")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")


class APIKeyCreate(APIKeyBase):
    """Model for creating new API key."""
    pass


class APIKeyResponse(BaseModel):
    """Model for API key response."""
    id: str
    name: str
    description: Optional[str] = None
    key_preview: str = Field(..., description="First 8 chars of the API key for identification")
    user_id: str
    user_tier: UserTier
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True
    usage_count: int = 0
    monthly_usage: int = 0
    
    class Config:
        from_attributes = True


class APIKeyUpdate(BaseModel):
    """Model for updating API key."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class UsageStats(BaseModel):
    """Model for usage statistics."""
    user_id: str
    user_tier: UserTier
    total_requests: int
    monthly_requests: int
    daily_requests: int
    last_request: Optional[datetime] = None
    monthly_limit: int
    daily_limit: int
    

class UsageLimitExceeded(BaseModel):
    """Model for usage limit exceeded response."""
    error: str = "usage_limit_exceeded"
    message: str
    current_usage: int
    limit: int
    user_tier: UserTier
    upgrade_message: Optional[str] = None


class UnauthUsageResponse(BaseModel):
    """Model for unauthenticated user usage response."""
    remaining_requests: int
    total_allowed: int = 5
    message: str
    upgrade_prompt: Optional[str] = None


# Tier limits configuration
TIER_LIMITS = {
    UserTier.UNAUTH: {
        "monthly_limit": 5,
        "daily_limit": 5,
        "description": "Unauthenticated user"
    },
    UserTier.FREE: {
        "monthly_limit": 100,
        "daily_limit": 25,
        "description": "Free tier user"
    },
    UserTier.PREMIUM: {
        "monthly_limit": -1,  # -1 means unlimited
        "daily_limit": -1,    # -1 means unlimited
        "description": "Premium tier user"
    }
}

# Response messages
TIER_MESSAGES = {
    UserTier.UNAUTH: {
        "limit_exceeded": "You've reached the limit for anonymous users. Please login or create an account for more requests.",
        "upgrade_prompt": "Create a free account to get 100 requests per month!"
    },
    UserTier.FREE: {
        "limit_exceeded": "You've reached your monthly limit of 100 requests. Upgrade to Premium for unlimited access.",
        "upgrade_prompt": "Upgrade to Premium for unlimited requests!"
    },
    UserTier.PREMIUM: {
        "limit_exceeded": "Unlimited access - you shouldn't see this message",
        "upgrade_prompt": None
    }
}