"""
Pomodoro Recommendation Router
Recommend optimal pomodoro intervals based on persona
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional

from app.schemas.requests import PomodoroRequest
from app.schemas.responses import PomodoroResponse, ErrorResponse
from app.services.model_loader import model_loader
from app.utils.auth import verify_api_key
from app.utils.logger import logger


router = APIRouter()


@router.get(
    "/recommend",
    response_model=PomodoroResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Invalid API Key"},
        422: {"model": ErrorResponse, "description": "Invalid persona"},
        500: {"model": ErrorResponse, "description": "Recommendation failed"}
    },
    summary="Get Pomodoro Recommendation",
    description="Get personalized pomodoro timer recommendation based on user persona"
)
async def recommend_pomodoro(
    persona: str = Query(..., description="User persona"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get pomodoro recommendation
    
    **Query Parameters:**
    - persona: User learning persona
      - consistent_learner
      - fast_learner
      - new_learner
      - reflective_learner
    
    **Returns:**
    - focus_minutes: Recommended focus duration (minutes)
    - rest_minutes: Recommended rest duration (minutes)
    - rationale: Explanation for the recommendation
    - persona: User persona used
    
    **Recommendations:**
    - `fast_learner`: 25 min focus / 5 min rest (Classic Pomodoro)
    - `consistent_learner`: 30 min focus / 5 min rest (Slightly longer)
    - `reflective_learner`: 45 min focus / 10 min rest (Deep work)
    - `new_learner`: 20 min focus / 5 min rest (Gentle start)
    """
    
    try:
        logger.info(f"⏱️  Pomodoro recommendation request for: {persona}")
        
        # Validate persona
        valid_personas = ['consistent_learner', 'fast_learner', 'new_learner', 'reflective_learner']
        if persona not in valid_personas:
            raise ValueError(f"Invalid persona. Must be one of: {valid_personas}")
        
        # Load pomodoro recommender
        recommender = model_loader.get_model("pomodoro_recommender")
        
        # Get recommendation
        recommendation = recommender.recommend(persona)
        
        logger.info(f"✅ Recommended: {recommendation['focus_minutes']}min focus / {recommendation['rest_minutes']}min rest")
        
        return PomodoroResponse(
            focus_minutes=recommendation['focus_minutes'],
            rest_minutes=recommendation['rest_minutes'],
            rationale=recommendation['rationale'],
            persona=persona
        )
        
    except ValueError as e:
        logger.error(f"❌ Invalid persona: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"❌ Pomodoro recommendation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(e)}"
        )


@router.post(
    "/recommend",
    response_model=PomodoroResponse,
    summary="Get Pomodoro Recommendation (POST)",
    description="Alternative POST endpoint for pomodoro recommendation"
)
async def recommend_pomodoro_post(
    request: PomodoroRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Get pomodoro recommendation via POST
    
    Alternative endpoint that accepts POST with JSON body.
    Useful when additional user data is needed for adjustment.
    """
    
    return await recommend_pomodoro(persona=request.persona, api_key=api_key)


@router.get(
    "/presets",
    summary="Get Pomodoro Presets",
    description="Get all available pomodoro presets for each persona"
)
async def get_pomodoro_presets(api_key: str = Depends(verify_api_key)):
    """
    Get all pomodoro presets
    """
    
    return {
        "presets": [
            {
                "persona": "fast_learner",
                "focus_minutes": 25,
                "rest_minutes": 5,
                "description": "Classic Pomodoro - Quick bursts of focused work"
            },
            {
                "persona": "consistent_learner",
                "focus_minutes": 30,
                "rest_minutes": 5,
                "description": "Extended focus - Steady learning rhythm"
            },
            {
                "persona": "reflective_learner",
                "focus_minutes": 45,
                "rest_minutes": 10,
                "description": "Deep work - Extended concentration periods"
            },
            {
                "persona": "new_learner",
                "focus_minutes": 20,
                "rest_minutes": 5,
                "description": "Gentle start - Building focus habits"
            }
        ]
    }
