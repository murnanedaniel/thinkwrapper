"""Authentication routes for OAuth login/logout."""
from flask import Blueprint, redirect, url_for, session, jsonify, request, current_app
from flask_login import login_user, logout_user, login_required, current_user

from .auth import oauth
from .models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def get_db_session():
    """Get database session from app context."""
    return current_app.db_session_factory()


@auth_bp.route('/login')
def login():
    """Initiate Google OAuth login."""
    # Store the page the user came from so we can redirect back
    next_url = request.args.get('next', '/')
    session['next_url'] = next_url
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

        db = get_db_session()
        user = db.query(User).filter_by(
            oauth_provider='google',
            oauth_id=user_info['sub']
        ).first()

        if not user:
            user = User(
                email=user_info['email'],
                name=user_info.get('name'),
                oauth_provider='google',
                oauth_id=user_info['sub']
            )
            db.add(user)
            db.commit()

        login_user(user)

        # Redirect to where the user came from
        next_url = session.pop('next_url', '/')
        return redirect(next_url)


    except Exception as e:
        current_app.logger.error(f"OAuth callback error: {str(e)}")
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
    """Get current user info including subscription status."""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'email': current_user.email,
            'name': current_user.name,
            'id': current_user.id,
            'subscription_status': current_user.subscription_status,
            'has_subscription': current_user.subscription_status == 'active',
        })
    return jsonify({'authenticated': False})
