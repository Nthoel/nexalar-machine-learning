"""
Weekly Insights Router
Generate weekly learning insights and recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime

from app.schemas.requests import InsightRequest
from app.schemas.responses import InsightResponse, ErrorResponse
from app.services.model_loader import model_loader
from app.utils.auth import verify_api_key
from app.utils.logger import logger


router = APIRouter()


@router.post(
    "/weekly",
    response_model=InsightResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Invalid API Key"},
        500: {"model": ErrorResponse, "description": "Generation failed"}
    },
    summary="Generate Weekly Insights",
    description="Generate weekly learning insights with engagement score and recommendations"
)
async def generate_weekly_insights(
    request: InsightRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Generate weekly learning insights
    
    **Weekly Metrics Required:**
    - total_study_time_hours: Total study time in hours
    - pomodoro_sessions: Number of pomodoro sessions completed
    - quizzes_completed: Number of quizzes completed
    - modules_finished: Number of modules finished
    
    **Optional:**
    - previous_week_data: Previous week's data for comparison
    
    **Returns:**
    - engagement_score: Overall engagement score (0-100)
    - performance_level: Performance category (excellent/good/average/needs_improvement)
    - improvement_rate: Week-over-week improvement percentage
    - recommendations: List of actionable recommendations
    - summary: Human-readable summary
    - metrics: Detailed metrics breakdown
    - persona: User persona
    """
    
    try:
        logger.info("📊 Generating weekly insights")
        
        # Load insight generator
        generator = model_loader.get_model("insight_generator")
        
        # Generate insights
        insights = generator.generate(request.weekly_data, request.persona)
        
        # Calculate improvement rate if previous week data available
        improvement_rate = 0.0
        if request.previous_week_data:
            try:
                prev_generator = model_loader.get_model("insight_generator")
                prev_insights = prev_generator.generate(
                    request.previous_week_data, 
                    request.persona
                )
                
                current_score = insights['engagement_score']
                prev_score = prev_insights['engagement_score']
                
                if prev_score > 0:
                    improvement_rate = ((current_score - prev_score) / prev_score) * 100
                
            except Exception as e:
                logger.warning(f"Could not calculate improvement rate: {e}")
        
        # Generate human-readable summary
        level = insights['performance_level']
        score = insights['engagement_score']
        
        summary_templates = {
            'excellent': f"Outstanding performance this week! Your engagement score of {score:.1f}/100 shows exceptional dedication.",
            'good': f"Great work this week! Your engagement score of {score:.1f}/100 demonstrates solid progress.",
            'average': f"You're making progress with an engagement score of {score:.1f}/100. Let's aim higher next week!",
            'needs_improvement': f"Your engagement score of {score:.1f}/100 shows room for improvement. Let's build better habits together!"
        }
        
        summary = summary_templates.get(level, f"Your weekly engagement score: {score:.1f}/100")
        
        logger.info(f"✅ Insights generated: {level} ({score:.1f}/100)")
        
        return InsightResponse(
            engagement_score=insights['engagement_score'],
            performance_level=insights['performance_level'],
            improvement_rate=round(improvement_rate, 2),
            recommendations=insights['recommendations'],
            summary=summary,
            metrics=insights['metrics'],
            persona=request.persona
        )
        
    except Exception as e:
        logger.error(f"❌ Insight generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Insight generation failed: {str(e)}"
        )


@router.get(
    "/performance-levels",
    summary="Get Performance Levels",
    description="Get performance level definitions and thresholds"
)
async def get_performance_levels(api_key: str = Depends(verify_api_key)):
    """
    Get performance level definitions
    """
    
    return {
        "levels": [
            {
                "level": "excellent",
                "score_range": "85-100",
                "description": "Outstanding engagement and progress",
                "badge": "🌟"
            },
            {
                "level": "good",
                "score_range": "70-84",
                "description": "Solid performance with consistent progress",
                "badge": "👍"
            },
            {
                "level": "average",
                "score_range": "50-69",
                "description": "Moderate engagement with room for growth",
                "badge": "📈"
            },
            {
                "level": "needs_improvement",
                "score_range": "0-49",
                "description": "Low engagement, needs focus on building habits",
                "badge": "💪"
            }
        ]
    }
