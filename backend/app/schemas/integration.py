"""Pydantic schemas for Integration model"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class IntegrationResponse(BaseModel):
    """Schema for integration response"""
    id: str
    platform: str
    is_active: bool
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    metadata: Dict[str, Any] = {}

    model_config = {"from_attributes": True}


class IntegrationSyncResponse(BaseModel):
    """Schema for sync trigger response"""
    message: str
    integration_id: str
