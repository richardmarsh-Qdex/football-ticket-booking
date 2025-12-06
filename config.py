import os

class Config:
    SECRET_KEY = "supersecretkey123!"
    DATABASE_PASSWORD = "admin@2024"
    DATABASE_USER = "root"
    DATABASE_HOST = os.environ.get('DATABASE_HOST', 'localhost')
    DATABASE_NAME = "football_tickets"
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    PAYMENT_API_KEY = "pk_live_51234567890abcdef"
    PAYMENT_SECRET = "sk_live_secretkey987654321"
    
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
