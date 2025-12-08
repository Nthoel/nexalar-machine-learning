"""
Pydantic request models for API validation
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class PersonaFeaturesRequest(BaseModel):
    """Request model for persona prediction"""
    
    features: Dict[str, Any] = Field(
        ...,
        description="User features (18 features required)"
    )


class NotificationRequest(BaseModel):
    """Request model for notification generation"""
    
    user_id: str = Field(..., description="User ID")
    persona: str = Field(..., description="User persona")
    user_data: Dict[str, Any] = Field(..., description="User activity data")


class InsightRequest(BaseModel):
    """Request model for weekly insights"""
    
    weekly_data: Dict[str, Any] = Field(..., description="Weekly activity data")
    persona: str = Field(..., description="User persona")
    previous_week_data: Optional[Dict[str, Any]] = Field(None, description="Previous week data")


class PomodoroRequest(BaseModel):
    """Request model for pomodoro recommendation"""
    
    persona: str = Field(..., description="User persona")
    user_data: Optional[Dict[str, Any]] = Field(None, description="Optional user data")
