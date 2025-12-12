"""
Persona Prediction Router
"""

from datetime import datetime
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.requests import (
    PersonaFeaturesRequest,
    PersonaFromWeeklyRequest,
)
from app.schemas.responses import PersonaResponse
from app.services.model_loader import model_loader
from app.utils.auth import verify_api_key
from app.utils.logger import logger

router = APIRouter()

PERSONA_LABELS = {
    0: "consistent_learner",
    1: "fast_learner",
    2: "new_learner",
    3: "reflective_learner",
}

# Reverse mapping for string predictions
PERSONA_LABELS_REVERSE = {v: v for v in PERSONA_LABELS.values()}


# ==========
# UTILITIES
# ==========

def extract_features_array(features_dict: Dict[str, Any]) -> np.ndarray:
    """
    OLD MODE: Extract flat feature dict into numpy array (existing flow).
    Tetap dipakai untuk endpoint /predict/persona yang lama.
    """
    feature_order = [
        "total_activities",
        "completion_rate",
        "consistency_ratio",
        "avg_study_duration_min",
        "total_completions",
        "avg_session_gap_days",
        "active_days",
        "total_study_time_hours",
        "peak_hour",
        "weekend_activity_ratio",
        "late_night_study_ratio",
        "morning_study_ratio",
        "focus_score",
        "streak_days",
        "quiz_attempt_rate",
        "material_review_rate",
        "pomodoro_usage_rate",
        "dominant_time_period",
    ]

    try:
        features = []
        for key in feature_order:
            if key not in features_dict:
                raise ValueError(f"Missing required feature: '{key}'")

            value = features_dict[key]

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


def aggregate_features_from_weekly(weekly_reports: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    NEW MODE: Aggregate array weekly_reports dari backend menjadi 1 vector fitur.
    weekly_reports berisi field-field dari tabel weekly_reports.
    """
    df = pd.DataFrame(weekly_reports)

    if df.empty:
        raise ValueError("weekly_reports is empty")

    feats = {
        "avg_study_duration_min": df["avg_session_duration"].mean(),
        "std_study_duration_min": df["avg_session_duration"].std() or 0.0,
        "total_study_time_4weeks_min": df["total_study_time_hours"].sum() * 60.0,
        "total_activities": df["total_activities"].sum(),
        "engagement_score": df["engagement_score"].mean(),
        "completion_rate": df["completion_rate"].mean(),
        "total_completed": df["quizzes_completed"].sum() + df["modules_finished"].sum(),
        "total_submissions": df["quizzes_completed"].sum(),
        "total_completions": df["modules_finished"].sum(),
        "quiz_completion_rate": df["quiz_completion_rate"].mean(),
        "avg_quiz_score": df["quiz_avg_score"].mean(),
        "module_completion_rate": df["module_completion_rate"].mean(),
        "avg_time_per_module": df["avg_time_per_module"].mean(),
        "consistency_score": df["consistency_score"].mean(),
        "avg_response_time": df["avg_response_time"].mean(),
        "help_request_frequency": df["help_request_frequency"].sum(),
        "revisit_rate": df["revisit_rate"].mean(),
        "avg_break_duration": df["avg_break_duration"].mean(),
    }

    # ganti NaN → 0
    feats = {k: 0.0 if pd.isna(v) else float(v) for k, v in feats.items()}
    return feats


def map_weekly_to_model_features(weekly_feats: Dict[str, float]) -> Dict[str, float]:
    """
    Map aggregated weekly features ke 18 model features yang dibutuhkan
    oleh model persona lama.
    """
    consistency = weekly_feats.get("consistency_score", 0.0)
    if consistency <= 0:
        consistency = 0.1

    return {
        "total_activities": weekly_feats.get("total_activities", 0.0),
        "completion_rate": weekly_feats.get("completion_rate", 0.0),
        "consistency_ratio": weekly_feats.get("consistency_score", 0.0),
        "avg_study_duration_min": weekly_feats.get("avg_study_duration_min", 0.0),
        "total_completions": weekly_feats.get("total_completions", 0.0),
        "avg_session_gap_days": 7.0 / consistency,
        "active_days": weekly_feats.get("total_activities", 0.0) * 0.8,
        "total_study_time_hours": weekly_feats.get(
            "total_study_time_4weeks_min", 0.0
        )
        / 60.0,
        "peak_hour": 14.0,
        "weekend_activity_ratio": 0.3,
        "late_night_study_ratio": 0.2,
        "morning_study_ratio": 0.3,
        "focus_score": weekly_feats.get("engagement_score", 0.0),
        "streak_days": weekly_feats.get("consistency_score", 0.0) * 28.0,
        "quiz_attempt_rate": weekly_feats.get("quiz_completion_rate", 0.0),
        "material_review_rate": weekly_feats.get("revisit_rate", 0.0),
        "pomodoro_usage_rate": 0.5,
        "dominant_time_period": 2.0,
    }


def run_persona_model(model_features: Dict[str, float]) -> Dict[str, Any]:
    """
    Jalankan model persona dari 18 model features.
    Menghasilkan persona, confidence, dan pomodoro config.
    """
    model = model_loader.get_model("persona_model")
    scaler = model_loader.get_model("persona_scaler")

    if not model or not scaler:
        raise RuntimeError("Persona model or scaler not loaded")

    feature_order = [
        "total_activities",
        "completion_rate",
        "consistency_ratio",
        "avg_study_duration_min",
        "total_completions",
        "avg_session_gap_days",
        "active_days",
        "total_study_time_hours",
        "peak_hour",
        "weekend_activity_ratio",
        "late_night_study_ratio",
        "morning_study_ratio",
        "focus_score",
        "streak_days",
        "quiz_attempt_rate",
        "material_review_rate",
        "pomodoro_usage_rate",
        "dominant_time_period",
    ]

    x = np.array([model_features[f] for f in feature_order], dtype=np.float64).reshape(
        1, -1
    )

    x_scaled = scaler.transform(x)
    prediction = model.predict(x_scaled)
    predicted_value = prediction[0]

    # mapping label dari model
    if isinstance(predicted_value, (int, np.integer)):
        predicted_class = int(predicted_value)
        persona = PERSONA_LABELS.get(predicted_class, "unknown")
    elif isinstance(predicted_value, str):
        persona = (
            predicted_value
            if predicted_value in PERSONA_LABELS_REVERSE
            else "unknown"
        )
    else:
        persona = str(predicted_value)

    # probability / confidence
    try:
        probabilities = model.predict_proba(x_scaled)[0]
        if isinstance(predicted_value, (int, np.integer)):
            confidence = float(probabilities[int(predicted_value)])
        else:
            confidence = float(np.max(probabilities))
    except Exception:
        confidence = 1.0

    # ----- rule-based override untuk kasus ekstrem -----
    # Fast learner: aktivitas & skor sangat tinggi, konsistensi kuat
    if (
        model_features["total_activities"] >= 60
        and model_features["completion_rate"] >= 0.85
        and model_features["focus_score"] >= 0.85
        and model_features["quiz_attempt_rate"] >= 0.85
    ):
        persona = "fast_learner"

    # Reflective learner: durasi sesi panjang, revisit tinggi, tidak buru-buru
    elif (
        model_features["avg_study_duration_min"] >= 45
        and model_features["material_review_rate"] >= 0.5
        and model_features["focus_score"] >= 0.7
        and model_features["quiz_attempt_rate"] >= 0.6
    ):
        persona = "reflective_learner"

    # Consistent learner: konsistensi tinggi, jam belajar cukup
    elif (
        model_features["consistency_ratio"] >= 0.8
        and model_features["total_study_time_hours"] >= 8
        and model_features["completion_rate"] >= 0.6
    ):
        persona = "consistent_learner"

    # New learner: aktivitas & skor rendah
    elif (
        model_features["total_activities"] <= 10
        and model_features["completion_rate"] <= 0.4
        and model_features["focus_score"] <= 0.4
    ):
        persona = "new_learner"

    # Pomodoro config sederhana per persona
    pomodoro_defaults = {
        "new_learner": {"focus": 20, "short_break": 5, "long_break": 15},
        "fast_learner": {"focus": 25, "short_break": 5, "long_break": 15},
        "consistent_learner": {"focus": 30, "short_break": 5, "long_break": 20},
        "reflective_learner": {"focus": 45, "short_break": 10, "long_break": 25},
    }
    cfg = pomodoro_defaults.get(persona, pomodoro_defaults["new_learner"])

    result = {
        "persona": persona,
        "confidence": round(confidence, 4),
        "pomodoro_focus": cfg["focus"],
        "pomodoro_short_break": cfg["short_break"],
        "pomodoro_long_break": cfg["long_break"],
        "predicted_at": datetime.utcnow(),
    }

    return result


# ==========
# OLD ENDPOINT (tetap ada)
# ==========

@router.post("/persona", response_model=PersonaResponse)
async def predict_persona(
    request: PersonaFeaturesRequest,
    api_key: str = Depends(verify_api_key),
):
    """OLD MODE: Predict user learning persona dari flat feature dict."""
    try:
        logger.info("🔮 Persona prediction request received (flat features)")

        # Extract & validate features
        try:
            features_array = extract_features_array(request.features)
        except ValueError as e:
            logger.error(f"❌ Feature validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )

        logger.debug(f"Features shape: {features_array.shape}")

        # Load model & scaler
        model = model_loader.get_model("persona_model")
        scaler = model_loader.get_model("persona_scaler")

        if not model or not scaler:
            raise HTTPException(status_code=500, detail="Model not loaded")

        # Scale & predict
        features_scaled = scaler.transform(features_array)
        prediction = model.predict(features_scaled)
        predicted_value = prediction[0]

        if isinstance(predicted_value, (int, np.integer)):
            predicted_class = int(predicted_value)
            persona = PERSONA_LABELS.get(predicted_class, "unknown")
        elif isinstance(predicted_value, str):
            persona = (
                predicted_value
                if predicted_value in PERSONA_LABELS_REVERSE
                else "unknown"
            )
        else:
            persona = str(predicted_value)

        # Confidence
        try:
            probabilities = model.predict_proba(features_scaled)[0]
            if isinstance(predicted_value, (int, np.integer)):
                confidence = float(probabilities[int(predicted_value)])
            else:
                confidence = float(np.max(probabilities))
        except Exception:
            confidence = 1.0
            logger.warning(
                "Model doesn't support predict_proba, using confidence 1.0"
            )

        logger.info(f"✅ Prediction: {persona} (confidence: {confidence:.2f})")

        return PersonaResponse(
            persona=persona,
            confidence=round(confidence, 4),
            model_version="1.0.0",
            predicted_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Prediction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )


# ==========
# NEW ENDPOINT: DARI WEEKLY REPORTS
# ==========

@router.post("/persona/from-weekly")
async def predict_persona_from_weekly(
    request: PersonaFromWeeklyRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    NEW MODE:
    - Backend kirim JSON weekly_reports dari database.
    - Router:
      1) agregasi weekly_reports → weekly_aggregated
      2) map ke 18 model features
      3) jalankan model + rule override
    """
    try:
        logger.info(
            f"🔮 Persona prediction from weekly reports for {request.user_email} "
            f"({len(request.weekly_reports)} weeks)"
        )

        weekly_feats = aggregate_features_from_weekly(
            [w.dict() for w in request.weekly_reports]
        )
        model_feats = map_weekly_to_model_features(weekly_feats)
        result = run_persona_model(model_feats)

        logger.info(
            f"✅ Prediction (from-weekly): {result['persona']} "
            f"(confidence: {result['confidence']:.2f})"
        )

        return {
            "success": True,
            "data": result,
            "features": {
                "weekly_aggregated": {
                    k: round(v, 3) for k, v in weekly_feats.items()
                },
                "model_mapped": {k: round(v, 3) for k, v in model_feats.items()},
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Prediction from weekly failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction from weekly failed: {str(e)}",
        )


@router.get("/persona/labels")
async def get_persona_labels(api_key: str = Depends(verify_api_key)):
    """Get all available persona labels"""
    return {
        "personas": [
            {
                "label": "consistent_learner",
                "description": "Regular study habits, steady progress",
            },
            {
                "label": "fast_learner",
                "description": "Quick completion, high engagement",
            },
            {
                "label": "new_learner",
                "description": "Just started, building habits",
            },
            {
                "label": "reflective_learner",
                "description": "Deep thinking, thorough learning",
            },
        ]
    }
