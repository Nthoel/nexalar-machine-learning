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


def generate_extended_message(persona: str, performance_level: str, metrics: dict, engagement_score: float) -> str:
    """
    Generate a dynamic extended message (1 paragraph with 3 sentences) based on persona and progress.
    
    Sentence 1: Persona-based insight about learning style
    Sentence 2: Progress-specific feedback based on metrics
    Sentence 3: Personalized tip/encouragement
    """
    
    # --- Sentence 1: Persona-based insight ---
    persona_insights = {
        'fast_learner': "As a Fast Learner, you thrive on quick absorption of new concepts and enjoy tackling challenges head-on.",
        'consistent_learner': "As a Consistent Learner, your steady and disciplined approach helps you build strong foundations over time.",
        'reflective_learner': "As a Reflective Learner, you excel at deep thinking and connecting ideas in meaningful ways.",
        'new_learner': "As a New Learner, you're just beginning your journey and every step forward is a valuable achievement."
    }
    # Normalize persona key
    persona_key = persona.lower().replace(' ', '_') if persona else 'new_learner'
    sentence_1 = persona_insights.get(persona_key, "Your unique learning style is shaping your educational journey in interesting ways.")
    
    # --- Sentence 2: Progress-specific feedback ---
    study_time = metrics.get('study_time', 0) if metrics else 0
    pomodoro = metrics.get('pomodoro', 0) if metrics else 0
    quizzes = metrics.get('quizzes', 0) if metrics else 0
    modules = metrics.get('modules', 0) if metrics else 0
    
    # Build progress sentence based on actual data
    progress_parts = []
    if study_time > 0:
        progress_parts.append(f"logged {study_time:.1f} hours of study time")
    if pomodoro > 0:
        progress_parts.append(f"completed {pomodoro} Pomodoro session{'s' if pomodoro > 1 else ''}")
    if quizzes > 0:
        progress_parts.append(f"finished {quizzes} quiz{'zes' if quizzes > 1 else ''}")
    if modules > 0:
        progress_parts.append(f"progressed through {modules} module{'s' if modules > 1 else ''}")
    
    if progress_parts:
        if len(progress_parts) == 1:
            progress_detail = progress_parts[0]
        elif len(progress_parts) == 2:
            progress_detail = f"{progress_parts[0]} and {progress_parts[1]}"
        else:
            progress_detail = f"{', '.join(progress_parts[:-1])}, and {progress_parts[-1]}"
        
        if performance_level == 'excellent':
            sentence_2 = f"This week you've {progress_detail} — an outstanding achievement that puts you ahead of the curve!"
        elif performance_level == 'good':
            sentence_2 = f"This week you've {progress_detail}, showing solid commitment to your learning goals."
        elif performance_level == 'average':
            sentence_2 = f"This week you've {progress_detail}, which is a good foundation to build upon."
        else:  # needs_improvement
            sentence_2 = f"This week you've {progress_detail} — every bit of progress counts toward your success."
    else:
        sentence_2 = "This week is a fresh start — begin with small steps and watch your progress grow."
    
    # --- Sentence 3: Personalized tip based on persona + performance ---
    tips = {
        ('fast_learner', 'excellent'): "Keep pushing your limits by exploring advanced topics or setting stretch goals for next week!",
        ('fast_learner', 'good'): "Consider challenging yourself with more complex materials to maintain your momentum.",
        ('fast_learner', 'average'): "Try breaking larger goals into smaller sprints to reignite your fast-paced learning style.",
        ('fast_learner', 'needs_improvement'): "Start with quick wins — short, focused sessions can help you regain your learning rhythm.",
        
        ('consistent_learner', 'excellent'): "Your consistency is paying off — consider mentoring others or tackling a passion project!",
        ('consistent_learner', 'good'): "Maintain your steady pace and perhaps add one new learning technique to your routine.",
        ('consistent_learner', 'average'): "Try scheduling your study sessions at the same time each day to strengthen your habits.",
        ('consistent_learner', 'needs_improvement'): "Focus on rebuilding your routine — even 15 minutes daily can restart your consistent progress.",
        
        ('reflective_learner', 'excellent'): "Your deep understanding is impressive — share your insights through notes or discussions to solidify learning!",
        ('reflective_learner', 'good'): "Take time to review and connect this week's concepts with what you've learned before.",
        ('reflective_learner', 'average'): "Try journaling about what you learn — it aligns perfectly with your reflective nature.",
        ('reflective_learner', 'needs_improvement'): "Start with revisiting previous materials — your strength lies in making deep connections.",
        
        ('new_learner', 'excellent'): "Amazing start! You're building great habits — keep exploring and stay curious!",
        ('new_learner', 'good'): "You're making wonderful progress as a beginner — celebrate these early wins!",
        ('new_learner', 'average'): "Every expert was once a beginner — keep experimenting to find what works best for you.",
        ('new_learner', 'needs_improvement'): "Take it one step at a time — focus on understanding rather than speed, and you'll get there."
    }
    
    tip_key = (persona_key, performance_level)
    sentence_3 = tips.get(tip_key, "Keep up the effort and stay committed to your learning journey!")
    
    # Combine into one paragraph
    extended_message = f"{sentence_1} {sentence_2} {sentence_3}"
    
    return extended_message


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
    - extended_message: Dynamic motivational paragraph for "Say More" section
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
        
        # Generate extended message for "Say More" section
        extended_message = generate_extended_message(
            persona=request.persona,
            performance_level=level,
            metrics=insights['metrics'],
            engagement_score=score
        )
        
        logger.info(f"✅ Insights generated: {level} ({score:.1f}/100)")
        
        return InsightResponse(
            engagement_score=insights['engagement_score'],
            performance_level=insights['performance_level'],
            improvement_rate=round(improvement_rate, 2),
            recommendations=insights['recommendations'],
            summary=summary,
            extended_message=extended_message,
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
