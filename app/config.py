"""
Configuration management with Pydantic Settings
Auto-load from .env file
"""

from pydantic_settings import BaseSettings
from typing import List
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
