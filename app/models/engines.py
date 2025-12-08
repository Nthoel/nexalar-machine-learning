"""
Model engine classes for non-ML models
These classes need to be importable for joblib to load pickled objects
"""

from datetime import datetime, timedelta, timezone
import random
from typing import Dict, Any


class NotificationEngine:
    """Rule-based notification generator"""
    
    def __init__(self):
        self.notification_templates = {
            'encouragement': [
                "🌟 Great progress, {name}! Keep up the momentum!",
                "💪 You're doing amazing! {achievement}",
                "🎯 Stay focused! You're on the right track!",
                "✨ {name}, your consistency is inspiring!"
            ],
            'reminder': [
                "⏰ Hey {name}, time to continue your learning journey!",
                "📚 Don't forget your study session today!",
                "🔔 {name}, you haven't studied in {days} days. Ready to jump back in?",
                "💡 Quick reminder: Your learning goal is waiting!"
            ],
            'achievement': [
                "🎉 Congratulations {name}! You've completed {milestone}!",
                "🏆 Amazing! You just finished {achievement}!",
                "⭐ Milestone reached! {milestone} completed!",
                "🎊 Well done! {achievement} unlocked!"
            ],
            'tip': [
                "💡 Pro tip: {tip_content}",
                "🎓 Did you know? {tip_content}",
                "📖 Learning tip: {tip_content}",
                "🔑 Key insight: {tip_content}"
            ],
            'streak': [
                "🔥 {streak_days} day streak! Don't break it!",
                "⚡ Awesome! {streak_days} consecutive days of learning!",
                "🌟 You're on fire! {streak_days} day streak going strong!"
            ]
        }
        
        self.learning_tips = [
            "Take regular breaks to improve retention",
            "Review concepts multiple times for better understanding",
            "Practice active recall instead of passive reading",
            "Teach others to solidify your knowledge",
            "Set specific goals before each study session"
        ]
    
    def generate(self, user_data: dict, persona: str) -> dict:
        """Generate notification"""
        
        last_activity = user_data.get('last_activity_date', datetime.now(timezone.utc))
        
        # Convert string to datetime if needed
        if isinstance(last_activity, str):
            try:
                # Parse ISO format with timezone
                if 'Z' in last_activity:
                    last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                else:
                    last_activity = datetime.fromisoformat(last_activity)
                    # Make timezone aware if naive
                    if last_activity.tzinfo is None:
                        last_activity = last_activity.replace(tzinfo=timezone.utc)
            except:
                last_activity = datetime.now(timezone.utc)
        
        # Make sure last_activity is timezone aware
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)
        
        # Use timezone-aware datetime for comparison
        now = datetime.now(timezone.utc)
        days_since = (now - last_activity).days
        
        consistency = user_data.get('consistency_ratio', 0)
        completions = user_data.get('total_completions', 0)
        
        # Determine type
        if days_since >= 3:
            notif_type = 'reminder'
            priority = 'high'
        elif completions > 0 and completions % 5 == 0:
            notif_type = 'achievement'
            priority = 'high'
        elif consistency < 0.3:
            notif_type = 'reminder'
            priority = 'medium'
        elif persona == 'new_learner':
            notif_type = 'encouragement'
            priority = 'medium'
        else:
            notif_type = 'tip'
            priority = 'low'
        
        # Generate message
        template = random.choice(self.notification_templates[notif_type])
        message = template.replace('{name}', user_data.get('user_name', 'Learner'))
        message = message.replace('{days}', str(days_since))
        message = message.replace('{achievement}', f"{completions} courses")
        message = message.replace('{milestone}', f"{completions} modules")
        message = message.replace('{tip_content}', random.choice(self.learning_tips))
        message = message.replace('{streak_days}', str(user_data.get('streak_days', 0)))
        
        # Best time
        peak_hour = user_data.get('peak_hour', 14)
        if persona == 'fast_learner':
            best_time = max(6, peak_hour - 2)
        elif persona == 'reflective_learner':
            best_time = min(20, peak_hour + 2)
        else:
            best_time = peak_hour
        
        return {
            'type': notif_type,
            'message': message,
            'best_time_hour': best_time,
            'priority': priority
        }


class InsightGenerator:
    """Formula-based insight generator"""
    
    def __init__(self):
        self.weights = {
            'study_time': 0.30,
            'pomodoro': 0.25,
            'quizzes': 0.20,
            'modules': 0.25
        }
        
        self.targets = {
            'study_time_hours': 10,
            'pomodoro_sessions': 20,
            'quizzes_completed': 5,
            'modules_finished': 10
        }
    
    def generate(self, weekly_data: dict, persona: str) -> dict:
        """Generate insights from weekly data"""
        
        study_hours = weekly_data.get('total_study_time_hours', 0)
        pomodoro = weekly_data.get('pomodoro_sessions', 0)
        quizzes = weekly_data.get('quizzes_completed', 0)
        modules = weekly_data.get('modules_finished', 0)
        
        study_score = min(100, (study_hours / self.targets['study_time_hours']) * 100)
        pomodoro_score = min(100, (pomodoro / self.targets['pomodoro_sessions']) * 100)
        quiz_score = min(100, (quizzes / self.targets['quizzes_completed']) * 100)
        module_score = min(100, (modules / self.targets['modules_finished']) * 100)
        
        engagement_score = (
            study_score * self.weights['study_time'] +
            pomodoro_score * self.weights['pomodoro'] +
            quiz_score * self.weights['quizzes'] +
            module_score * self.weights['modules']
        )
        
        if engagement_score >= 85:
            level = 'excellent'
        elif engagement_score >= 70:
            level = 'good'
        elif engagement_score >= 50:
            level = 'average'
        else:
            level = 'needs_improvement'
        
        recommendations = []
        if study_hours < 5:
            recommendations.append("📚 Increase study time to at least 5 hours/week")
        if pomodoro < 10:
            recommendations.append("⏱️ Use Pomodoro technique for better focus")
        if quizzes < 2:
            recommendations.append("✅ Complete more quizzes to test understanding")
        if modules < 5:
            recommendations.append("🎯 Finish at least 5 modules per week")
        
        if persona == 'new_learner':
            recommendations.append("🌱 Start small: Build consistent daily habits")
        elif persona == 'fast_learner':
            recommendations.append("🚀 Challenge yourself with advanced topics")
        
        if not recommendations:
            recommendations.append("🌟 Keep up the excellent work!")
        
        return {
            'engagement_score': round(engagement_score, 2),
            'performance_level': level,
            'recommendations': recommendations[:5],
            'metrics': {
                'study_time': study_hours,
                'pomodoro': pomodoro,
                'quizzes': quizzes,
                'modules': modules
            }
        }


class AdaptivePomodoro:
    """Adaptive pomodoro recommender based on persona"""
    
    def __init__(self):
        self.recommendations = {
            'fast_learner': {
                'focus_minutes': 25,
                'rest_minutes': 5,
                'rationale': 'Classic Pomodoro - Quick bursts work well for fast learners who maintain high energy'
            },
            'consistent_learner': {
                'focus_minutes': 30,
                'rest_minutes': 5,
                'rationale': 'Extended focus - Your consistent habits allow for slightly longer concentration periods'
            },
            'reflective_learner': {
                'focus_minutes': 45,
                'rest_minutes': 10,
                'rationale': 'Deep work sessions - Your reflective nature benefits from longer, uninterrupted thinking time'
            },
            'new_learner': {
                'focus_minutes': 20,
                'rest_minutes': 5,
                'rationale': 'Gentle start - Shorter sessions help build focus habits without overwhelming'
            }
        }
    
    def recommend(self, persona: str, user_data: dict = None) -> dict:
        """Get pomodoro recommendation for persona"""
        
        recommendation = self.recommendations.get(
            persona,
            self.recommendations['consistent_learner']
        )
        
        if user_data and 'avg_study_duration_min' in user_data:
            avg_duration = user_data['avg_study_duration_min']
            if avg_duration > 60:
                recommendation['focus_minutes'] = min(60, recommendation['focus_minutes'] + 10)
        
        return recommendation
