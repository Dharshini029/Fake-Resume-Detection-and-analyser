import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fake-resume-detector-college-key-2026-xyz')
    DATABASE_PATH = BASE_DIR / 'data' / 'resumes.db'
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    DEMO_FOLDER = BASE_DIR / 'demo_resumes'
    MODELS_DIR = BASE_DIR / 'models'
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    
    # Risk Scoring Thresholds
    RISK_LOW_MAX = 35
    RISK_MODERATE_MAX = 69
    
    # Weights for Hybrid Score
    WEIGHT_RULES = 0.55
    WEIGHT_ML = 0.45

    # Server settings
    HOST = '127.0.0.1'
    PORT = 5000
    DEBUG = True
