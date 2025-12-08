"""
Notification Generation Router
Generate personalized notifications based on user behavior and persona
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import random

from app.schemas.requests import NotificationRequest
from app.schemas.responses import NotificationResponse, ErrorResponse
from app.services.model_loader import model_loader
from app.utils.auth import verify_api_key
from app.utils.logger import logger


router = APIRouter()


@router.post(
    "/generate",
    response_model=NotificationResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Invalid API Key"},
        500: {"model": ErrorResponse, "description": "Generation failed"}
    },
    summary="Generate Notification",
    description="Generate personalized notification based on user behavior and persona"
)
async def generate_notification(
    request: NotificationRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Generate personalized notification
    
    **Notification Types:**
    - `encouragement`: Motivational messages
    - `reminder`: Study reminders
    - `achievement`: Milestone celebrations
    - `tip`: Learning tips
    - `streak`: Streak maintenance
    
    **Request Body:**
    - user_id: User identifier
    - persona: User persona (consistent_learner, fast_learner, etc.)
    - user_data: Dictionary with user activity data
      - user_name: User's name (optional)
      - last_activity_date: Last activity timestamp
      - consistency_ratio: Consistency score (0-1)
      - total_completions: Total completed activities
      - peak_hour: Most active hour (0-23)
      - streak_days: Current streak (optional)
    
    **Returns:**
    - type: Notification type
    - message: Notification message
    - best_time_hour: Best hour to send (0-23)
    - priority: Priority level (low/medium/high)
    - generated_at: Timestamp
    """
    
    try:
        logger.info(f"🔔 Generating notification for user: {request.user_id}")
        
        # Load notification engine
        engine = model_loader.get_model("notification_engine")
        
        # Parse last_activity_date if string
        user_data = request.user_data.copy()
        if isinstance(user_data.get('last_activity_date'), str):
            try:
                user_data['last_activity_date'] = datetime.fromisoformat(
                    user_data['last_activity_date'].replace('Z', '+00:00')
                )
            except:
                user_data['last_activity_date'] = datetime.utcnow()
        
        # Generate notification
        notification = engine.generate(user_data, request.persona)
        
        logger.info(f"✅ Notification generated: {notification['type']}")
        
        return NotificationResponse(
            type=notification['type'],
            message=notification['message'],
            best_time_hour=notification['best_time_hour'],
            priority=notification['priority'],
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"❌ Notification generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Notification generation failed: {str(e)}"
        )


@router.get(
    "/types",
    summary="Get Notification Types",
    description="Get list of available notification types"
)
async def get_notification_types(api_key: str = Depends(verify_api_key)):
    """
    Get all available notification types with descriptions
    """
    
    return {
        "types": [
            {
                "type": "encouragement",
                "description": "Motivational messages to boost morale",
                "use_case": "Regular positive reinforcement"
            },
            {
                "type": "reminder",
                "description": "Study reminders for inactive users",
                "use_case": "When user hasn't studied in 3+ days"
            },
            {
                "type": "achievement",
                "description": "Celebrate milestones and completions",
                "use_case": "When user completes significant progress"
            },
            {
                "type": "tip",
                "description": "Learning tips and best practices",
                "use_case": "General educational content"
            },
            {
                "type": "streak",
                "description": "Streak maintenance notifications",
                "use_case": "Encourage continued consistency"
            }
        ]
    }
