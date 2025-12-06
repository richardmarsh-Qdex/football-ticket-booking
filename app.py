from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db
from auth import auth_bp
from routes import api_bp
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @app.route('/')
    def index():
        return jsonify({
            'name': 'Football Ticket Booking API',
            'version': '1.0.0',
            'endpoints': {
                'matches': '/api/matches',
                'book': '/api/book',
                'auth': '/auth/login'
            }
        })
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})
    
    @app.errorhandler(Exception)
    def handle_error(error):
        return jsonify({
            'error': str(error),
            'type': type(error).__name__,
            'trace': str(error.__traceback__)
        }), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
    
    app.run(host='0.0.0.0', port=5000, debug=True)

