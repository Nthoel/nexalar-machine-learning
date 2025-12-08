"""
Recreate model pickle files with proper class definitions
Run this once to fix the 3 failed models
"""

import joblib
import os
from app.models.engines import NotificationEngine, InsightGenerator, AdaptivePomodoro

def recreate_models():
    """Recreate all non-ML model pickle files"""
    
    print("="*60)
    print("🔧 RECREATING MODEL FILES")
    print("="*60)
    
    # Create models directory if not exists
    os.makedirs('models/notification', exist_ok=True)
    os.makedirs('models/insight', exist_ok=True)
    os.makedirs('models/pomodoro', exist_ok=True)
    
    # 1. Notification Engine
    print("\n📧 Creating Notification Engine...")
    notification_engine = NotificationEngine()
    joblib.dump(notification_engine, 'models/notification/notification_engine.pkl')
    print("✅ Saved: models/notification/notification_engine.pkl")
    
    # 2. Insight Generator
    print("\n📊 Creating Insight Generator...")
    insight_generator = InsightGenerator()
    joblib.dump(insight_generator, 'models/insight/insight_generator.pkl')
    print("✅ Saved: models/insight/insight_generator.pkl")
    
    # 3. Pomodoro Recommender
    print("\n⏱️  Creating Pomodoro Recommender...")
    pomodoro_recommender = AdaptivePomodoro()
    joblib.dump(pomodoro_recommender, 'models/pomodoro/pomodoro_recommender.pkl')
    print("✅ Saved: models/pomodoro/pomodoro_recommender.pkl")
    
    print("\n" + "="*60)
    print("✅ ALL MODELS RECREATED SUCCESSFULLY!")
    print("="*60)
    
    # Test loading
    print("\n🧪 Testing model loading...")
    try:
        test_notif = joblib.load('models/notification/notification_engine.pkl')
        test_insight = joblib.load('models/insight/insight_generator.pkl')
        test_pomodoro = joblib.load('models/pomodoro/pomodoro_recommender.pkl')
        print("✅ All models load successfully!")
    except Exception as e:
        print(f"❌ Error loading models: {e}")

if __name__ == "__main__":
    recreate_models()
