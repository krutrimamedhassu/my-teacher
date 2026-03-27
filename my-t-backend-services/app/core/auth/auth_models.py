from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re
from app.core.auth.api_key_models import UserTier


class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    """Model for user registration."""
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v


class UserLogin(BaseModel):
    """Model for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Model for updating user information."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    profile_image_url: Optional[str] = Field(None, max_length=500)
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if v is not None and not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v


class PasswordUpdate(BaseModel):
    """Model for password update."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class EmailUpdate(BaseModel):
    """Model for email update."""
    current_password: str
    new_email: EmailStr


class UserResponse(BaseModel):
    """Model for user response (without sensitive data)."""
    id: str
    email: EmailStr
    username: str
    full_name: str
    profile_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Model for authentication token response."""
    message: str
    user: UserResponse


class AuthResponse(BaseModel):
    """Model for authentication response."""
    message: str
    user: UserResponse 


class UserTierUpdate(BaseModel):
    """Model for updating a user's subscription tier."""
    tier: UserTier