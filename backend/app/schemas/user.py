"""Pydantic schemas for User model"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100)
    team_id: Optional[str] = None
    role: Optional[str] = "developer"  # Default role is developer


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response (without password)"""
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    timezone: str
    role: str
    is_active: bool
    is_verified: bool
    team_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class TokenPayload(BaseModel):
    """Schema for decoded token payload"""
    sub: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for password reset"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
