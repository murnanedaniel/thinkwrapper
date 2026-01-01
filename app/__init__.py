from flask import Flask
import os

def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder='static')
    
    # Configure secret key for sessions
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Load configuration
    if test_config is None:
        # Load the instance config when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
    
    # Initialize OAuth
    from .auth import init_oauth, init_login_manager
    oauth_client = init_oauth(app)
    login_manager = init_login_manager(app)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from .auth_routes import get_db_session
        from .models import User
        db = get_db_session()
        try:
            return db.query(User).get(int(user_id))
        finally:
            db.close()
    
    # Register blueprints
    from . import routes
    app.register_blueprint(routes.bp)
    
    from . import auth_routes
    app.register_blueprint(auth_routes.auth_bp)
    
    # A simple route to check if the app is running
    @app.route('/health')
    def health():
        return {'status': 'ok'}
        
    return app 