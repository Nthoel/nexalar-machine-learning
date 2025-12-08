# Nexalar ML Service

Machine learning microservice for Nexalar Learning Platform.

## Features

- Persona Prediction: Classify learners into 4 personas
- Smart Notifications: Generate personalized notifications  
- Weekly Insights: Calculate engagement scores
- Adaptive Pomodoro: Recommend optimal study intervals

## Quick Start

### 1. Install Dependencies

pip install -r requirements.txt

Edit .env with your settings.

### 3. Run Server

uvicorn app.main:app --reload --port 8000

### 4. Access API Docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check
GET /health

### Persona Prediction
POST /predict/persona

### Notification Generation
POST /notification/generate

### Weekly Insights
POST /insight/weekly

### Pomodoro Recommendation
GET /pomodoro/recommend

## Authentication

All endpoints require API key in header:
X-API-Key: your-api-key-here

## Deployment

See Railway deployment guide below.

## Tech Stack

- FastAPI 0.109.0
- Python 3.11.9
- scikit-learn 1.4.0
- XGBoost 2.0.3

## License

Private - Nexalar Learning Platform
