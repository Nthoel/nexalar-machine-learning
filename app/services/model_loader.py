"""
ML Model loader with caching
Load models once at startup, cache in memory
"""

import joblib
import os
from typing import Dict, Any, Optional
from app.config import settings
from app.utils.logger import logger


class ModelLoader:
    """Singleton model loader with caching"""
    
    _instance: Optional['ModelLoader'] = None
    _models: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize model cache"""
        if not self._models:
            logger.info("🔧 Initializing ModelLoader...")
    
    def load_model(self, model_name: str, model_path: str) -> Any:
        """
        Load model from disk or return from cache
        
        Args:
            model_name: Name identifier for caching
            model_path: Path to .pkl file
        
        Returns:
            Loaded model object
        """
        
        # Return from cache if exists
        if settings.model_cache_enabled and model_name in self._models:
            logger.debug(f"✅ Model '{model_name}' loaded from cache")
            return self._models[model_name]
        
        # Check if file exists
        if not os.path.exists(model_path):
            logger.warning(f"⚠️  Model file not found: {model_path}")
            return None
        
        try:
            logger.info(f"📂 Loading model from: {model_path}")
            model = joblib.load(model_path)
            
            # Cache the model
            if settings.model_cache_enabled:
                self._models[model_name] = model
                logger.info(f"✅ Model '{model_name}' loaded and cached")
            
            return model
            
        except Exception as e:
            logger.error(f"❌ Failed to load model '{model_name}': {e}")
            return None
    
    def load_all_models(self) -> Dict[str, bool]:
        """
        Load all models at startup
        
        Returns:
            Dict with model names and load status
        """
        
        logger.info("="*60)
        logger.info("🚀 LOADING ALL ML MODELS")
        logger.info("="*60)
        
        status = {}
        
        # Persona Model & Scaler (CRITICAL)
        try:
            persona_model = self.load_model("persona_model", settings.persona_model_path)
            persona_scaler = self.load_model("persona_scaler", settings.persona_scaler_path)
            
            if persona_model and persona_scaler:
                status["persona"] = True
                logger.info("✅ Persona model loaded")
            else:
                status["persona"] = False
                logger.error("❌ Persona model failed")
        except Exception as e:
            status["persona"] = False
            logger.error(f"❌ Persona model failed: {e}")
        
        # Notification Engine (Rule-based, may fail due to class definition)
        try:
            notification = self.load_model("notification_engine", settings.notification_model_path)
            if notification:
                status["notification"] = True
                logger.info("✅ Notification engine loaded")
            else:
                # Fallback: Create basic notification engine
                logger.warning("⚠️  Notification engine not loaded, using fallback")
                status["notification"] = False
        except Exception as e:
            status["notification"] = False
            logger.warning(f"⚠️  Notification engine failed: {e}")
        
        # Insight Generator (Formula-based, may fail due to class definition)
        try:
            insight = self.load_model("insight_generator", settings.insight_model_path)
            if insight:
                status["insight"] = True
                logger.info("✅ Insight generator loaded")
            else:
                logger.warning("⚠️  Insight generator not loaded, using fallback")
                status["insight"] = False
        except Exception as e:
            status["insight"] = False
            logger.warning(f"⚠️  Insight generator failed: {e}")
        
        # Pomodoro Recommender (Lookup table, may fail due to class definition)
        try:
            pomodoro = self.load_model("pomodoro_recommender", settings.pomodoro_model_path)
            if pomodoro:
                status["pomodoro"] = True
                logger.info("✅ Pomodoro recommender loaded")
            else:
                logger.warning("⚠️  Pomodoro recommender not loaded, using fallback")
                status["pomodoro"] = False
        except Exception as e:
            status["pomodoro"] = False
            logger.warning(f"⚠️  Pomodoro recommender failed: {e}")
        
        logger.info("="*60)
        logger.info(f"✅ Models loaded: {sum(status.values())}/{len(status)}")
        logger.info("="*60)
        
        # Only fail if critical persona model is not loaded
        if not status.get("persona"):
            logger.error("❌ CRITICAL: Persona model not loaded!")
        
        return status
    
    def get_model(self, model_name: str) -> Any:
        """
        Get cached model
        
        Args:
            model_name: Name of the model
        
        Returns:
            Cached model object or None
        """
        
        return self._models.get(model_name)


# Global model loader instance
model_loader = ModelLoader()
