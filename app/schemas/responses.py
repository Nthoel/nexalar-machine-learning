"""
Pydantic response models for API
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Any, Optional
from datetime import datetime


class PersonaResponse(BaseModel):
    """Response model for persona prediction"""
    
    persona: str = Field(..., description="Predicted persona")
    confidence: float = Field(..., description="Prediction confidence (0-1)")
    model_version: str = Field(..., description="Model version")
    predicted_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "persona": "fast_learner",
                "confidence": 0.92,
                "model_version": "1.0.0",
                "predicted_at": "2025-12-08T01:30:00Z"
            }
        },
        protected_namespaces=()
    )


class NotificationResponse(BaseModel):
    """Response model for notification generation"""
    
    type: str = Field(..., description="Notification type")
    message: str = Field(..., description="Notification message")
    best_time_hour: int = Field(..., description="Best hour to send (0-23)")
    priority: str = Field(..., description="Priority level")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class InsightResponse(BaseModel):
    """Response model for weekly insights"""
    
    engagement_score: float = Field(..., description="Engagement score (0-100)")
    performance_level: str = Field(..., description="Performance level")
    improvement_rate: float = Field(..., description="Week-over-week improvement %")
    recommendations: List[str] = Field(..., description="Actionable recommendations")
    summary: str = Field(..., description="Human-readable summary")
    metrics: Dict[str, Any] = Field(..., description="Detailed metrics")
    week_number: Optional[int] = Field(None, description="Week number")
    persona: str = Field(..., description="User persona")


class PomodoroResponse(BaseModel):
    """Response model for pomodoro recommendation"""
    
    focus_minutes: int = Field(..., description="Focus duration in minutes")
    rest_minutes: int = Field(..., description="Rest duration in minutes")
    rationale: str = Field(..., description="Explanation")
    persona: str = Field(..., description="User persona")


class HealthResponse(BaseModel):
    """Response model for health check"""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    models_loaded: Dict[str, bool] = Field(..., description="Model load status")
    uptime: Optional[str] = Field(None, description="Service uptime")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Response model for errors"""
    
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
