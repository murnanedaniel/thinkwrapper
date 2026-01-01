# Implement Google OAuth Authentication

**Labels**: `feature`, `authentication`, `security`, `high-priority`

## Overview
Implement Google OAuth 2.0 authentication to allow users to sign up and log in to ThinkWrapper.

## Objectives
- Set up Google OAuth 2.0 integration
- Implement user authentication flow
- Create user session management
- Add protected routes requiring authentication
- Store user information in database

## Technical Requirements

### Google Cloud Setup
- [ ] Create Google Cloud project
- [ ] Enable Google OAuth 2.0 API
- [ ] Configure OAuth consent screen
- [ ] Create OAuth 2.0 credentials (client ID & secret)
- [ ] Add authorized redirect URIs

### Backend Implementation
- [ ] Install authlib library (already in requirements.txt)
- [ ] Configure OAuth client in Flask app
- [ ] Create authentication blueprint/routes:
  - `GET /auth/login` - Initiate OAuth flow
  - `GET /auth/callback` - Handle OAuth callback
  - `GET /auth/logout` - Log out user
  - `GET /auth/user` - Get current user info
- [ ] Implement user session management with Flask-Login
- [ ] Add login_required decorator for protected routes

### Database Integration
- [ ] User model already has google_id, name, profile_pic fields
- [ ] Create or update user on successful OAuth
- [ ] Store OAuth tokens securely (if needed for API access)
- [ ] Handle account linking (email already exists)

### Frontend Integration
- [ ] Add "Sign in with Google" button
- [ ] Handle OAuth redirect flow
- [ ] Store user session/token
- [ ] Display user profile information
- [ ] Add logout functionality
- [ ] Protect routes requiring authentication

### Security Considerations
- [ ] Validate OAuth state parameter (CSRF protection)
- [ ] Use secure session cookies
- [ ] Implement proper token validation
- [ ] Add rate limiting to auth endpoints
- [ ] Log authentication events
- [ ] Handle token refresh if needed

### Testing
- [ ] Unit tests for auth routes
- [ ] Test OAuth callback handling
- [ ] Test session management
- [ ] Test protected route access
- [ ] Test logout functionality
- [ ] Mock Google OAuth for testing

### Documentation
- [ ] Document OAuth setup process
- [ ] Add environment variable documentation
- [ ] User authentication flow diagram
- [ ] API endpoint documentation

## Example Implementation

```python
# app/auth.py
from flask import Blueprint, redirect, url_for, session
from flask_login import login_user, logout_user, login_required
from authlib.integrations.flask_client import OAuth
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth client."""
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
        client_kwargs={'scope': 'openid email profile'}
    )

@auth_bp.route('/login')
def login():
    """Initiate Google OAuth login."""
    redirect_uri = url_for('auth.callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/callback')
def callback():
    """Handle OAuth callback."""
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')

    # Find or create user
    user = User.query.filter_by(google_id=user_info['sub']).first()
    if not user:
        user = User(
            google_id=user_info['sub'],
            email=user_info['email'],
            name=user_info.get('name'),
            profile_pic=user_info.get('picture')
        )
        db.session.add(user)
        db.session.commit()

    # Log in user
    login_user(user)
    return redirect(url_for('index'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out user."""
    logout_user()
    return redirect(url_for('index'))

@auth_bp.route('/user')
@login_required
def get_user():
    """Get current user info."""
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
        'profile_pic': current_user.profile_pic
    })
```

## Frontend Example

```javascript
// Login button
<button onClick={() => window.location.href = '/auth/login'}>
  Sign in with Google
</button>

// Check auth status
useEffect(() => {
  fetch('/auth/user')
    .then(res => res.ok ? res.json() : null)
    .then(user => setCurrentUser(user))
    .catch(() => setCurrentUser(null));
}, []);
```

## OAuth Flow
1. User clicks "Sign in with Google"
2. Redirect to Google OAuth consent screen
3. User approves access
4. Google redirects to `/auth/callback` with authorization code
5. Exchange code for access token and user info
6. Create/update user in database
7. Create session and log in user
8. Redirect to dashboard

## Acceptance Criteria
- [ ] Users can sign in with Google account
- [ ] User information stored in database
- [ ] Sessions persist across requests
- [ ] Protected routes require authentication
- [ ] Logout works correctly
- [ ] Tests achieve >80% coverage
- [ ] Security best practices followed
- [ ] Documentation complete

## Related Issues
- Depends on: None (User model ready)
- Blocks: All user-facing features

## Estimated Effort
Medium (2-3 days)

## Resources
- [Google OAuth 2.0 Docs](https://developers.google.com/identity/protocols/oauth2)
- [Authlib Documentation](https://docs.authlib.org/en/latest/client/flask.html)
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
