"""Authentication service for Google OAuth."""
import os
from authlib.integrations.flask_client import OAuth
from flask import url_for, session
from flask_login import LoginManager

# Initialize OAuth
oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth client with Google configuration."""
    oauth.init_app(app)
    
    # Register Google OAuth
    google = oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    
    return google

def init_login_manager(app):
    """Initialize Flask-Login."""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    return login_manager
