"""
Configuration management with Pydantic Settings
Auto-load from .env file
"""

from pydantic_settings import BaseSettings
from typing import List, Dict, Any
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application Info
    app_name: str = "Nexalar ML Service"
    app_version: str = "1.0.0"
    environment: str = "development"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = True
    
    # Security
    api_key: str = "nexalar-ml-api-key-2025"
    allowed_origins: str = "http://localhost:3000,http://localhost:5000,http://localhost:5173"
    
    # Model Paths
    model_dir: str = "./models"
    persona_model_path: str = "./models/persona/latest_model.pkl"
    persona_scaler_path: str = "./models/persona/latest_scaler.pkl"
    notification_model_path: str = "./models/notification/notification_engine.pkl"
    insight_model_path: str = "./models/insight/insight_generator.pkl"
    pomodoro_model_path: str = "./models/pomodoro/pomodoro_recommender.pkl"
    
    # Performance
    model_cache_enabled: bool = True
    request_timeout: int = 30
    max_request_size: int = 10485760  # 10MB
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "colorlog"
    
    # Feature Validation
    feature_count: int = 18
    strict_validation: bool = True
    
    # ================================
    # Weekly Reports Persona Config
    # ================================
    SELECTED_PERSONA_FEATURES: List[str] = [
        'total_activities',
        'completion_rate', 
        'consistency_score',
        'engagement_score',
        'total_study_time_hours',
        'quiz_completion_rate',
        'quiz_avg_score',
        'module_completion_rate',
        'avg_time_per_module',
        'avg_session_duration',
        'help_request_frequency',
        'revisit_rate',
        'avg_response_time',
        'avg_break_duration',
        'quizzes_completed',
        'modules_finished'
    ]
    
    PERSONA_CONFIG: Dict[str, Any] = {
        "personas": ["new_learner", "fast_learner", "consistent_learner", "reflective_learner"],
        "feature_weights": {
            'total_activities': 0.12,
            'completion_rate': 0.10,
            'consistency_score': 0.12,
            'engagement_score': 0.08,
            'total_study_time_hours': 0.10,
            'quiz_completion_rate': 0.08,
            'quiz_avg_score': 0.07,
            'module_completion_rate': 0.08,
            'avg_time_per_module': 0.06,
            'avg_session_duration': 0.05,
            'help_request_frequency': 0.04,
            'revisit_rate': 0.05,
            'avg_response_time': 0.03,
            'avg_break_duration': 0.02,
            'quizzes_completed': 0.05,
            'modules_finished': 0.05
        },
        "pomodoro_defaults": {
            "new_learner": {"focus": 20, "short_break": 5, "long_break": 15},
            "fast_learner": {"focus": 25, "short_break": 5, "long_break": 15},
            "consistent_learner": {"focus": 30, "short_break": 5, "long_break": 20},
            "reflective_learner": {"focus": 45, "short_break": 10, "long_break": 25}
        }
    }
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "protected_namespaces": ()  # Fix Pydantic warning
    }
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse allowed origins from comma-separated string"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"


# Global settings instance
settings = Settings()
