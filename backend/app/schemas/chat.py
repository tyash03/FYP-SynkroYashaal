"""Pydantic schemas for Chat"""
from pydantic import BaseModel
from typing import List, Dict, Any


class ChatQuerySchema(BaseModel):
    """Schema for chat query request"""
    message: str


class SuggestedAction(BaseModel):
    """Schema for a suggested action"""
    action: str
    label: str
    url: str


class ChatResponseSchema(BaseModel):
    """Schema for chat query response"""
    response: str
    context_used: Dict[str, Any]
    suggested_actions: List[SuggestedAction] = []
