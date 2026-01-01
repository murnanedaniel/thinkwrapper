from flask import Blueprint, jsonify, request, render_template, current_app, send_from_directory
from datetime import datetime
from .newsletter_synthesis import NewsletterSynthesizer, NewsletterRenderer, NewsletterConfig
from .services import send_email
from . import claude_service

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


@bp.route('/api/admin/synthesize', methods=['POST'])
def synthesize_newsletter():
    """
    Admin endpoint to trigger newsletter synthesis on demand.

    Expected JSON payload:
    {
        "newsletter_id": 1,
        "topic": "AI Weekly",
        "style": "professional",  // optional
        "format": "html",  // optional: html, text, both
        "send_email": false,  // optional
        "email_to": "admin@example.com"  // optional, required if send_email is true
    }
    """
    data = request.json

    # Validate required fields
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    newsletter_id = data.get('newsletter_id')
    topic = data.get('topic')

    if not newsletter_id:
        return jsonify({'error': 'newsletter_id is required'}), 400
    if not topic:
        return jsonify({'error': 'topic is required'}), 400

    # Optional parameters
    style = data.get('style', 'professional')
    output_format = data.get('format', 'html')
    send_email_flag = data.get('send_email', False)
    email_to = data.get('email_to')

    # Validate send_email requirements
    if send_email_flag and not email_to:
        return jsonify({'error': 'email_to is required when send_email is true'}), 400

    # Initialize synthesizer and renderer
    synthesizer = NewsletterSynthesizer()
    renderer = NewsletterRenderer()

    try:
        # Generate newsletter on demand
        result = synthesizer.generate_on_demand(
            newsletter_id=newsletter_id,
            topic=topic,
            style=style
        )

        if not result.get('success'):
            return jsonify({
                'error': 'Newsletter synthesis failed',
                'details': result.get('error')
            }), 500

        # Prepare content for rendering
        content = {
            'subject': result['subject'],
            'content': result['content']
        }

        # Render in requested format(s)
        rendered_output = {}

        if output_format == 'both':
            rendered_output['html'] = renderer.render_html(content)
            rendered_output['text'] = renderer.render_plain_text(content)
        elif output_format == 'text':
            rendered_output['text'] = renderer.render_plain_text(content)
        else:  # default to html
            rendered_output['html'] = renderer.render_html(content)

        # Send email if requested
        email_sent = False
        if send_email_flag:
            email_content = rendered_output.get('html') or rendered_output.get('text')
            email_sent = send_email(email_to, result['subject'], email_content)

        return jsonify({
            'success': True,
            'subject': result['subject'],
            'content': result['content'],
            'rendered': rendered_output,
            'metadata': {
                'content_items_count': result['content_items_count'],
                'generated_at': result['generated_at'],
                'style': result['style'],
                'format': output_format,
                'email_sent': email_sent
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Newsletter synthesis error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@bp.route('/api/admin/newsletter/config', methods=['GET', 'POST'])
def newsletter_config():
    """
    Get or update newsletter configuration settings.

    GET: Returns current configuration
    POST: Updates configuration with provided settings
    """
    config = NewsletterConfig()

    if request.method == 'GET':
        return jsonify(config.to_dict()), 200

    # POST - update configuration
    data = request.json
    if not data:
        return jsonify({'error': 'No configuration data provided'}), 400

    try:
        config.from_dict(data)
        is_valid, error_message = config.validate()

        if not is_valid:
            return jsonify({'error': error_message}), 400

        # In a real implementation, save config to database
        return jsonify({
            'success': True,
            'config': config.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Failed to update configuration',
            'details': str(e)
        }), 500


@bp.route('/api/admin/newsletter/preview', methods=['POST'])
def preview_newsletter():
    """
    Preview newsletter in different formats without sending.

    Expected JSON payload:
    {
        "subject": "Newsletter Subject",
        "content": "Newsletter content...",
        "format": "html"  // html, text, or both
    }
    """
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    subject = data.get('subject')
    content = data.get('content')
    output_format = data.get('format', 'html')

    if not subject or not content:
        return jsonify({'error': 'subject and content are required'}), 400

    renderer = NewsletterRenderer()
    content_dict = {'subject': subject, 'content': content}

    try:
        rendered_output = {}

        if output_format == 'both':
            rendered_output['html'] = renderer.render_html(content_dict)
            rendered_output['text'] = renderer.render_plain_text(content_dict)
        elif output_format == 'text':
            rendered_output['text'] = renderer.render_plain_text(content_dict)
        else:
            rendered_output['html'] = renderer.render_html(content_dict)

        return jsonify({
            'success': True,
            'rendered': rendered_output
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Preview generation failed',
            'details': str(e)
        }), 500


@bp.route('/api/claude/generate', methods=['POST'])
def claude_generate():
    """
    Generate text using Claude API (demo endpoint).

    Request body:
        {
            "prompt": "Your prompt text",
            "model": "claude-3-5-sonnet-20241022" (optional),
            "max_tokens": 1024 (optional),
            "temperature": 1.0 (optional),
            "system_prompt": "System prompt" (optional)
        }

    Response:
        {
            "success": true,
            "text": "Generated text...",
            "model": "claude-3-5-sonnet-20241022",
            "usage": {"input_tokens": 10, "output_tokens": 100}
        }
    """
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    # Optional parameters
    model = data.get('model', 'claude-3-5-sonnet-20241022')
    max_tokens = data.get('max_tokens', 1024)
    temperature = data.get('temperature', 1.0)
    system_prompt = data.get('system_prompt')

    # Generate text using Claude
    result = claude_service.generate_text(
        prompt=prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system_prompt=system_prompt
    )

    if result is None:
        return jsonify({
            'error': 'Failed to generate text. Check API key configuration.'
        }), 500

    return jsonify({
        'success': True,
        'text': result['text'],
        'model': result['model'],
        'usage': result['usage'],
        'stop_reason': result['stop_reason']
    }), 200

@bp.route('/api/claude/newsletter', methods=['POST'])
def claude_newsletter():
    """
    Generate newsletter content using Claude API (demo endpoint).

    Request body:
        {
            "topic": "Newsletter topic",
            "style": "professional" (optional),
            "max_tokens": 2000 (optional)
        }

    Response:
        {
            "success": true,
            "subject": "Newsletter subject",
            "content": "Newsletter body...",
            "model": "claude-3-5-sonnet-20241022",
            "usage": {"input_tokens": 50, "output_tokens": 500}
        }
    """
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    topic = data.get('topic', '')
    if not topic:
        return jsonify({'error': 'No topic provided'}), 400

    # Optional parameters
    style = data.get('style', 'professional')
    max_tokens = data.get('max_tokens', 2000)

    # Generate newsletter using Claude
    result = claude_service.generate_newsletter_content_claude(
        topic=topic,
        style=style,
        max_tokens=max_tokens
    )

    if result is None:
        return jsonify({
            'error': 'Failed to generate newsletter. Check API key configuration.'
        }), 500

    return jsonify({
        'success': True,
        'subject': result['subject'],
        'content': result['content'],
        'model': result['model'],
        'usage': result['usage']
    }), 200


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
