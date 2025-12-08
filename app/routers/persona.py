"""
Persona Prediction Router
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import numpy as np

from app.schemas.requests import PersonaFeaturesRequest
from app.schemas.responses import PersonaResponse, ErrorResponse
from app.services.model_loader import model_loader
from app.utils.auth import verify_api_key
from app.utils.logger import logger


router = APIRouter()


PERSONA_LABELS = {
    0: "consistent_learner",
    1: "fast_learner", 
    2: "new_learner",
    3: "reflective_learner"
}

# Reverse mapping for string predictions
PERSONA_LABELS_REVERSE = {v: v for v in PERSONA_LABELS.values()}


def extract_features_array(features_dict: dict) -> np.ndarray:
    """Extract features in correct order"""
    
    feature_order = [
        'total_activities', 'completion_rate', 'consistency_ratio',
        'avg_study_duration_min', 'total_completions', 'avg_session_gap_days',
        'active_days', 'total_study_time_hours', 'peak_hour',
        'weekend_activity_ratio', 'late_night_study_ratio', 'morning_study_ratio',
        'focus_score', 'streak_days', 'quiz_attempt_rate',
        'material_review_rate', 'pomodoro_usage_rate', 'dominant_time_period'
    ]
    
    try:
        features = []
        for key in feature_order:
            if key not in features_dict:
                raise ValueError(f"Missing required feature: '{key}'")
            
            value = features_dict[key]
            
            # Try to convert to float
            try:
                numeric_value = float(value)
                features.append(numeric_value)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Feature '{key}' must be numeric. "
                    f"Got {type(value).__name__}: '{value}'"
                )
        
        return np.array(features, dtype=np.float64).reshape(1, -1)
        
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error processing features: {str(e)}")


@router.post("/persona", response_model=PersonaResponse)
async def predict_persona(
    request: PersonaFeaturesRequest,
    api_key: str = Depends(verify_api_key)
):
    """Predict user learning persona"""
    
    try:
        logger.info("🔮 Persona prediction request received")
        
        # Load model and scaler
        model = model_loader.get_model("persona_model")
        scaler = model_loader.get_model("persona_scaler")
        
        if not model or not scaler:
            raise HTTPException(status_code=500, detail="Model not loaded")
        
        # Extract and validate features
        try:
            features_array = extract_features_array(request.features)
        except ValueError as e:
            logger.error(f"❌ Feature validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        logger.debug(f"Features shape: {features_array.shape}")
        
        # Scale features
        features_scaled = scaler.transform(features_array)
        
        # Predict
        prediction = model.predict(features_scaled)
        
        logger.debug(f"Raw prediction: {prediction}, type: {type(prediction[0])}")
        
        # Handle both integer and string predictions
        predicted_value = prediction[0]
        
        if isinstance(predicted_value, (int, np.integer)):
            # Integer prediction - use mapping
            predicted_class = int(predicted_value)
            persona = PERSONA_LABELS.get(predicted_class, "unknown")
        elif isinstance(predicted_value, str):
            # String prediction - use as is
            persona = predicted_value if predicted_value in PERSONA_LABELS_REVERSE else "unknown"
        else:
            # Numpy string or other type
            persona = str(predicted_value)
        
        # Get probabilities if available
        try:
            probabilities = model.predict_proba(features_scaled)
            predicted_proba = probabilities[0]
            
            # Find confidence for the predicted class
            if isinstance(predicted_value, (int, np.integer)):
                confidence = float(predicted_proba[int(predicted_value)])
            else:
                # For string predictions, use max probability
                confidence = float(np.max(predicted_proba))
        except:
            # Model doesn't support predict_proba (e.g., LabelEncoder was used)
            confidence = 1.0
            logger.warning("Model doesn't support predict_proba, using confidence 1.0")
        
        logger.info(f"✅ Prediction: {persona} (confidence: {confidence:.2f})")
        
        return PersonaResponse(
            persona=persona,
            confidence=round(confidence, 4),
            model_version="1.0.0",
            predicted_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Prediction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/persona/labels")
async def get_persona_labels(api_key: str = Depends(verify_api_key)):
    """Get all available persona labels"""
    return {
        "personas": [
            {"label": "consistent_learner", "description": "Regular study habits, steady progress"},
            {"label": "fast_learner", "description": "Quick completion, high engagement"},
            {"label": "new_learner", "description": "Just started, building habits"},
            {"label": "reflective_learner", "description": "Deep thinking, thorough learning"}
        ]
    }
