from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from config import Config
from models import db
from auth import auth_bp
from routes import api_bp
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({'error': e.description}), e.code

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        return jsonify({'error': 'An internal server error occurred'}), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
    
    app.run(host='127.0.0.1', port=5000)