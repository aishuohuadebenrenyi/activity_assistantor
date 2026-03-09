from flask import Flask
from flask_cors import CORS
from .config import Config
from .models import db
from .routes.auth import auth_bp
from .routes.activity import activity_bp
from .routes.participant import participant_bp
from .routes.user import user_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(activity_bp, url_prefix='/api/activities')
    app.register_blueprint(participant_bp, url_prefix='/api') # /api/activity_id/...
    app.register_blueprint(user_bp, url_prefix='/api/user')
    
    # Create DB tables
    with app.app_context():
        db.create_all()

    # Root route for health check
    @app.route('/')
    def index():
        return {
            "status": "online",
            "message": "Activity Assistant Backend API is running",
            "docs": "/api/activities"
        }
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)
