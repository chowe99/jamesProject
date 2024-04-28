import os

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'a_default_secret_key')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    # Default to localhost but allow override through environment variable
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    RESULT_BACKEND = os.getenv('RESULT_BACKEND', 'redis://localhost:6379/0')
    RESULTS_STORAGE = {}

