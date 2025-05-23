import os
from flask import Flask
from .models import db, User # Import User for Flask-Login
from flask_login import LoginManager # Import LoginManager
# from flask_cors import CORS  # Uncomment if you need CORS
# from flask_limiter import Limiter  # Uncomment if you want rate limiting
# from flask_limiter.util import get_remote_address
from sqlalchemy import inspect

def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder='static')
    
    # Load configuration
    if test_config is None:
        # Load the instance config when not testing
        # Fix for Heroku PostgreSQL: replace 'postgres:' with 'postgresql:'
        database_url = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')
        if database_url.startswith('postgres:'):
            database_url = database_url.replace('postgres:', 'postgresql:', 1)
            
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_secret_key'), # Needed for sessions
            SQLALCHEMY_DATABASE_URI=database_url,
            SQLALCHEMY_TRACK_MODIFICATIONS=False
        )
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
        # Ensure a default database URI for tests if not provided
        app.config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:')
        app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
        app.config.setdefault('SECRET_KEY', 'test_secret_key') # Ensure test key for tests

    # --- Production Security Settings ---
    if not app.debug and not app.testing:
        app.config.update(
            SESSION_COOKIE_SECURE=True,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',
            SESSION_COOKIE_DOMAIN=None,  # Let Flask determine the domain
            REMEMBER_COOKIE_SECURE=True,
            REMEMBER_COOKIE_HTTPONLY=True,
            REMEMBER_COOKIE_SAMESITE='Lax',
        )
        # Ensure Flask knows it's behind a proxy (Heroku)
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
        # Uncomment and configure if you need CORS (e.g. frontend on different domain)
        # from flask_cors import CORS
        # CORS(app, supports_credentials=True, origins=['https://yourfrontend.com'])
        # Uncomment and configure if you want rate limiting
        # limiter = Limiter(app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
    else:
        # Development settings - less strict
        app.config.update(
            SESSION_COOKIE_SECURE=False,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',
        )
    
    # Configure signed cookie sessions (Flask built-in)
    app.config.update(
        PERMANENT_SESSION_LIFETIME=1800,  # 30 minutes
        SESSION_COOKIE_NAME='thinkwrapper_session',  # Custom session name
    )

    # Initialize extensions
    db.init_app(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Redirect unauthenticated users to login
    # login_manager.login_message_category = "info" # Optional: for flashing messages

    @login_manager.user_loader
    def load_user(user_id):
        # Use db.session.get for SQLAlchemy 2.0 compatibility
        return db.session.get(User, int(user_id))

    # Create database tables if they don't exist (for development/testing)
    # For production, migrations (e.g. Flask-Migrate) are recommended.
    with app.app_context():
        # Check if tables already exist before trying to create them
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        if not existing_tables:
            db.create_all()
    
    # Register auth blueprint FIRST (before catch-all routes)
    from . import auth as auth_bp
    app.register_blueprint(auth_bp.bp, url_prefix='/auth')
    
    # Initialize Auth0
    auth_bp.init_auth0(app)
    
    # Register main routes (including catch-all) AFTER auth routes
    from . import routes
    app.register_blueprint(routes.bp)
    
    # A simple route to check if the app is running
    @app.route('/health')
    def health():
        return {'status': 'ok'}
    
    return app

# ---
# IMPORTANT: In production, set SECRET_KEY and all other secrets using Heroku config vars, e.g.:
# heroku config:set SECRET_KEY='your-very-strong-secret'
# heroku config:set OPENAI_API_KEY=...
# heroku config:set SENDGRID_API_KEY=...
# heroku config:set PADDLE_WEBHOOK_SECRET=...
# heroku config:set AUTH0_DOMAIN='dev-26w2jl00f1tc85cq.us.auth0.com'
# heroku config:set AUTH0_CLIENT_ID='Wo2xo4VE3fHctnAzRm1U6WIzXtNkgyUY'
# heroku config:set AUTH0_CLIENT_SECRET='YCbb7vmHqR7a_1Af-SbJ3A06EvIcGtuSpIOH1oiAcPPRf3fs058HGurr1U6bQano'
# --- 