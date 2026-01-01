from flask import Blueprint, jsonify, request, render_template, current_app, send_from_directory

bp = Blueprint('routes', __name__)

@bp.route('/')
def index():
    """Serve the SPA index page."""
    return send_from_directory(current_app.static_folder, 'index.html')

@bp.route('/api/generate', methods=['POST'])
def generate_newsletter():
    """Generate a newsletter based on the provided topic."""
    data = request.json
    topic = data.get('topic', '')
    
    if not topic:
        return jsonify({'error': 'No topic provided'}), 400
    
    # In MVP, generate synchronously; later move to Celery
    # from .services import generate_newsletter_content
    # content = generate_newsletter_content(topic)
    
    return jsonify({'status': 'processing', 'topic': topic}), 202

@bp.route('/api/payment/checkout', methods=['POST'])
def create_payment_checkout():
    """
    Create a Paddle checkout session for payment.
    
    Expected JSON payload:
    {
        "price_id": "pri_xxx",
        "customer_email": "user@example.com",
        "success_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel"
    }
    """
    from .payment_service import get_paddle_service
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    price_id = data.get('price_id')
    customer_email = data.get('customer_email')
    success_url = data.get('success_url')
    cancel_url = data.get('cancel_url')
    metadata = data.get('metadata', {})
    
    if not price_id or not customer_email or not success_url:
        return jsonify({
            'error': 'Missing required fields: price_id, customer_email, success_url'
        }), 400
    
    paddle_service = get_paddle_service()
    checkout_session = paddle_service.create_checkout_session(
        price_id=price_id,
        customer_email=customer_email,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata
    )
    
    if checkout_session:
        return jsonify({
            'status': 'success',
            'checkout_url': checkout_session.get('data', {}).get('url'),
            'session_id': checkout_session.get('data', {}).get('id')
        }), 200
    else:
        return jsonify({'error': 'Failed to create checkout session'}), 500

@bp.route('/api/payment/webhook', methods=['POST'])
def paddle_webhook():
    """
    Handle Paddle webhook notifications.
    
    This endpoint receives payment status updates from Paddle.
    Webhook signature is verified for security.
    """
    from .payment_service import get_paddle_service
    
    # Get raw payload and signature
    payload = request.get_data(as_text=True)
    signature = request.headers.get('Paddle-Signature', '')
    
    if not signature:
        current_app.logger.error("Webhook received without signature")
        return jsonify({'error': 'Missing signature'}), 400
    
    # Verify webhook signature
    paddle_service = get_paddle_service()
    if not paddle_service.verify_webhook_signature(payload, signature):
        current_app.logger.error("Invalid webhook signature")
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Parse webhook data
    try:
        webhook_data = request.json
        event_type = webhook_data.get('event_type')
        event_data = webhook_data.get('data', {})
        
        if not event_type:
            return jsonify({'error': 'Missing event_type'}), 400
        
        # Process the webhook event
        result = paddle_service.process_webhook_event(event_type, event_data)
        
        current_app.logger.info(
            f"Webhook processed: {event_type} - Result: {result.get('status')}"
        )
        
        return jsonify({
            'status': 'received',
            'event_type': event_type
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Webhook processing error: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@bp.route('/api/payment/subscription/<subscription_id>/cancel', methods=['POST'])
def cancel_subscription(subscription_id):
    """
    Cancel a subscription.
    
    Optional JSON payload:
    {
        "effective_date": "2024-12-31"  # ISO format, optional
    }
    """
    from .payment_service import get_paddle_service
    
    data = request.json or {}
    effective_date = data.get('effective_date')
    
    paddle_service = get_paddle_service()
    success = paddle_service.cancel_subscription(
        subscription_id=subscription_id,
        effective_date=effective_date
    )
    
    if success:
        return jsonify({
            'status': 'success',
            'message': 'Subscription cancelled'
        }), 200
    else:
        return jsonify({'error': 'Failed to cancel subscription'}), 500

# Catch-all to support client-side routing
@bp.route('/<path:path>')
def catch_all(path):
    """Serve static files or return index.html for client-side routing."""
    try:
        return send_from_directory(current_app.static_folder, path)
    except:
        return send_from_directory(current_app.static_folder, 'index.html') 