from flask import Blueprint, request, jsonify, current_app, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User
from .services import verify_paddle_webhook # Import the verification function
from .auth0_config import AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_CALLBACK_URL
from authlib.integrations.flask_client import OAuth
import json
from urllib.parse import urlencode
from datetime import datetime

bp = Blueprint('auth', __name__)

# Set up OAuth for Auth0
oauth = OAuth()
auth0 = oauth.register(
    'auth0',
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    api_base_url=f'https://{AUTH0_DOMAIN}',
    access_token_url=f'https://{AUTH0_DOMAIN}/oauth/token',
    authorize_url=f'https://{AUTH0_DOMAIN}/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    },
)

# Initialize OAuth with the app in __init__.py
def init_auth0(app):
    oauth.init_app(app)

@bp.route('/login')
def login():
    """Redirect to Auth0 login page"""
    # Ensure session persists for Auth0 state parameter
    session.permanent = True
    
    # Add debugging BEFORE the redirect
    current_app.logger.info(f"=== LOGIN START ===")
    current_app.logger.info(f"Session before login: {dict(session)}")
    current_app.logger.info(f"Session permanent: {session.permanent}")
    
    # Store a test value to verify session persistence
    session['login_timestamp'] = str(datetime.now())
    
    current_app.logger.info(f"Session after setting timestamp: {dict(session)}")
    
    return auth0.authorize_redirect(redirect_uri=AUTH0_CALLBACK_URL)

@bp.route('/callback')
def callback():
    """Handle the Auth0 callback - get and store tokens, log user in"""
    current_app.logger.info(f"=== CALLBACK START ===")
    current_app.logger.info(f"Session at callback: {dict(session)}")
    current_app.logger.info(f"Session permanent: {session.permanent}")
    current_app.logger.info(f"Login timestamp from session: {session.get('login_timestamp', 'MISSING')}")
    
    # Get the state parameter from the request
    state_from_request = request.args.get('state')
    current_app.logger.info(f"State from Auth0 callback: {state_from_request}")
    
    try:
        token = auth0.authorize_access_token()
        resp = auth0.get('userinfo')
        userinfo = resp.json()
        
        # Store Auth0 user info in session
        session['jwt_payload'] = userinfo
        session.permanent = True
        
        # Find or create user
        user = User.get_or_create_from_auth0(userinfo)
        
        # Log user in with Flask-Login
        login_user(user)
        
        current_app.logger.info(f"Successfully authenticated user: {user.email}")
        
        # Redirect to dashboard upon successful login
        return redirect('/dashboard')
    except Exception as e:
        current_app.logger.error(f"Auth callback error: {str(e)}")
        current_app.logger.error(f"Session keys at error: {list(session.keys())}")
        # Redirect to home with error message
        return redirect('/?error=auth_failed')

@bp.route('/logout')
@login_required
def logout():
    """Log out the user from both the app and Auth0"""
    # Clear Flask session
    session.clear()
    
    # Log out of Flask-Login
    logout_user()
    
    # Redirect to Auth0 logout endpoint
    params = {'returnTo': url_for('routes.index', _external=True), 'client_id': AUTH0_CLIENT_ID}
    return redirect(f'https://{AUTH0_DOMAIN}/v2/logout?{urlencode(params)}')

@bp.route('/status')
@login_required
def status():
    """Returns the current user's status."""
    return jsonify({
        'status': 'success',
        'user': {'id': current_user.id, 'email': current_user.email}
    })

@bp.route('/session-test')
def session_test():
    """Test route to check session functionality"""
    if 'test_counter' not in session:
        session['test_counter'] = 0
    session['test_counter'] += 1
    session.permanent = True
    
    return jsonify({
        'session_id': session.get('_id', 'no-id'),
        'test_counter': session['test_counter'],
        'session_keys': list(session.keys()),
        'permanent': session.permanent
    })

@bp.route('/paddle/webhook', methods=['POST'])
def paddle_webhook_route(): # Renamed for clarity
    """Handles incoming webhooks from Paddle, verifies signature, and processes data."""
    raw_request_body = request.get_data() # Get raw body for signature verification
    signature_header = request.headers.get('Paddle-Signature')

    if not verify_paddle_webhook(raw_request_body, signature_header):
        current_app.logger.warning("Paddle webhook verification failed.")
        return jsonify({'error': 'Invalid Paddle signature'}), 403

    webhook_data = request.json # Now that it's verified, parse JSON
    current_app.logger.info(f"Received verified Paddle webhook: {webhook_data.get('event_type')}")
    
    event_type = webhook_data.get('event_type')
    data = webhook_data.get('data')

    if not event_type or not data:
        current_app.logger.error("Paddle webhook missing event_type or data.")
        return jsonify({'error': 'Missing event_type or data in webhook payload'}), 400

    # Example processing (adjust based on actual Paddle Billing webhook structure)
    if event_type == 'subscription.created' or event_type == 'subscription.updated':
        user_email = data.get('customer', {}).get('email') 
        # Or data.get('customer_id') and then find user by paddle_customer_id if you store that.
        # Or data.get('passthrough') if you pass your internal user_id to Paddle checkout.
        paddle_subscription_id = data.get('id')
        status = data.get('status') # e.g., active, trialing, past_due, paused, canceled
        
        if not user_email or not paddle_subscription_id or not status:
            current_app.logger.error("Paddle webhook (subscription.*) missing required fields.")
            return jsonify({'error': 'Webhook payload for subscription event missing fields'}), 400

        user = User.query.filter_by(email=user_email).first()
        if user:
            user.subscription_id = paddle_subscription_id
            user.is_active = status == 'active' # Simplified: active if Paddle status is 'active'
            # user.paddle_customer_id = data.get('customer_id') # If available
            # user.subscription_status = status # Store detailed status
            db.session.add(user) # Use add for both new and existing objects to be persisted
            db.session.commit()
            current_app.logger.info(f"Updated subscription for {user_email} to {status}. Sub ID: {paddle_subscription_id}")
        else:
            # Handle case where a subscription webhook arrives for a user not yet in your DB.
            # This might happen if checkout happens before local registration.
            # Option 1: Create a placeholder user (might need more info from webhook or a follow-up step)
            # Option 2: Log and ignore, wait for user to register with that email.
            current_app.logger.warning(f"Paddle subscription webhook for unknown user email: {user_email}. Sub ID: {paddle_subscription_id}")
    
    elif event_type == 'subscription.canceled':
        paddle_subscription_id = data.get('id')
        if not paddle_subscription_id:
            current_app.logger.error("Paddle webhook (subscription.canceled) missing subscription id.")
            return jsonify({'error': 'Webhook payload for subscription.canceled missing id'}), 400
            
        user = User.query.filter_by(subscription_id=paddle_subscription_id).first()
        if user:
            user.is_active = False
            # user.subscription_status = 'canceled'
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"Canceled subscription for user {user.email}. Sub ID: {paddle_subscription_id}")
        else:
            current_app.logger.warning(f"Paddle subscription.canceled webhook for unknown subscription ID: {paddle_subscription_id}")
    
    # Add more event_type handlers as needed (e.g., payment_succeeded, payment_failed)

    return jsonify({'status': 'webhook processed'}), 200 