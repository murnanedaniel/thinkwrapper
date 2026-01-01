"""Authentication routes for OAuth login/logout."""
from flask import Blueprint, redirect, url_for, session, jsonify, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy import create_engine
import os

from .auth import oauth
from .models import User, Base

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def get_db_session():
    """Get database session from app context."""
    if not hasattr(current_app, 'db_session_factory'):
        database_url = os.getenv('DATABASE_URL', 'sqlite:///thinkwrapper.db')
        # Fix for Heroku postgres URL
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)
        current_app.db_session_factory = scoped_session(sessionmaker(bind=engine))
    
    return current_app.db_session_factory()

@auth_bp.route('/login')
def login():
    """Initiate Google OAuth login."""
    redirect_uri = url_for('auth.callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/callback')
def callback():
    """Handle Google OAuth callback."""
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            return jsonify({'error': 'Failed to get user info'}), 400
        
        # Get or create user
        db = get_db_session()
        try:
            user = db.query(User).filter_by(
                oauth_provider='google',
                oauth_id=user_info['sub']
            ).first()
            
            if not user:
                # Create new user
                user = User(
                    email=user_info['email'],
                    name=user_info.get('name'),
                    oauth_provider='google',
                    oauth_id=user_info['sub']
                )
                db.add(user)
                db.commit()
            
            # Log in the user
            login_user(user)
            
            # Redirect to frontend
            return redirect('/')
        finally:
            db.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    session.clear()
    return redirect('/')

@auth_bp.route('/user')
def get_user():
    """Get current user info."""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'email': current_user.email,
            'name': current_user.name,
            'id': current_user.id
        })
    return jsonify({'authenticated': False})
