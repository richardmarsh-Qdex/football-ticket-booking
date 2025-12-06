import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set")
    
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')
    if not DATABASE_PASSWORD:
        raise ValueError("DATABASE_PASSWORD environment variable must be set")
    
    DATABASE_USER = os.environ.get('DATABASE_USER', 'root')
    DATABASE_HOST = os.environ.get('DATABASE_HOST', 'localhost')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'football_tickets')
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    PAYMENT_API_KEY = os.environ.get('PAYMENT_API_KEY')
    if not PAYMENT_API_KEY:
        raise ValueError("PAYMENT_API_KEY environment variable must be set")
    
    PAYMENT_SECRET = os.environ.get('PAYMENT_SECRET')
    if not PAYMENT_SECRET:
        raise ValueError("PAYMENT_SECRET environment variable must be set")
    
    PAYMENT_API_BASE_URL = os.environ.get('PAYMENT_API_BASE_URL', 'https://api.paymentgateway.com')
    
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
