from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User
from .services import verify_paddle_webhook # Import the verification function

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email address already registered'}), 409 # Conflict

    new_user = User(email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    login_user(new_user) # Log in the user after registration
    return jsonify({
        'status': 'success',
        'message': 'User registered and logged in successfully.',
        'user': {'id': new_user.id, 'email': new_user.email}
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    if user is None or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    login_user(user)
    return jsonify({
        'status': 'success',
        'message': 'Logged in successfully.',
        'user': {'id': user.id, 'email': user.email}
    })

@bp.route('/logout', methods=['POST'])
@login_required # Ensure user is logged in to log out
def logout():
    logout_user()
    return jsonify({'status': 'success', 'message': 'Logged out successfully.'})

@bp.route('/status')
@login_required
def status():
    """Returns the current user's status."""
    return jsonify({
        'status': 'success',
        'user': {'id': current_user.id, 'email': current_user.email}
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