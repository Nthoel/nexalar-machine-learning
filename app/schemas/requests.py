"""
Pydantic request models for API validation
"""

from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field


class PersonaFeaturesRequest(BaseModel):
    """Request model for persona prediction"""

    features: Dict[str, Any] = Field(
        ...,
        description="User features (18 features required)",
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
    previous_week_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Previous week data",
    )


class PomodoroRequest(BaseModel):
    """Request model for pomodoro recommendation"""

    persona: str = Field(..., description="User persona")
    user_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional user data",
    )


# ================================
# Persona from weekly_reports
# ================================

class WeeklyReportItem(BaseModel):
    """Single weekly report entry used for persona prediction"""

    avg_session_duration: float = Field(
        ...,
        description="Average session duration in minutes for the week",
    )
    total_activities: int = Field(
        ...,
        description="Total number of learning activities",
    )
    engagement_score: float = Field(
        ...,
        description="Composite engagement score for the week",
    )
    total_study_time_hours: float = Field(
        ...,
        description="Total study time in hours",
    )
    completion_rate: float = Field(
        ...,
        description="Overall task/module completion rate (0-1)",
    )
    quiz_completion_rate: float = Field(
        ...,
        description="Quiz completion rate (0-1)",
    )
    quiz_avg_score: float = Field(
        ...,
        description="Average quiz score (0-100 or 0-1, depending on pipeline)",
    )
    module_completion_rate: float = Field(
        ...,
        description="Module completion rate (0-1)",
    )
    avg_time_per_module: float = Field(
        ...,
        description="Average time spent per module in minutes",
    )
    consistency_score: float = Field(
        ...,
        description="Weekly study consistency score",
    )
    avg_response_time: float = Field(
        ...,
        description="Average response time to prompts/notifications",
    )
    help_request_frequency: int = Field(
        ...,
        description="Number of help/support requests in the week",
    )
    revisit_rate: float = Field(
        ...,
        description="Rate of revisiting past materials (0-1)",
    )
    avg_break_duration: float = Field(
        ...,
        description="Average break duration in minutes",
    )
    quizzes_completed: int = Field(
        ...,
        description="Total quizzes completed in the week",
    )
    modules_finished: int = Field(
        ...,
        description="Total modules finished in the week",
    )


class PersonaFromWeeklyRequest(BaseModel):
    """Request model for persona prediction from raw weekly reports"""

    user_id: str = Field(..., description="User ID")
    user_email: str = Field(..., description="User email")
    weekly_reports: List[WeeklyReportItem] = Field(
        ...,
        description="Ordered list of weekly reports (oldest to newest)",
    )
