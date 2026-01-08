from flask import (
    Blueprint,
    jsonify,
    request,
    current_app,
    send_from_directory,
)
from datetime import datetime
import os
import uuid
import redis
from .newsletter_synthesis import NewsletterSynthesizer, NewsletterRenderer, NewsletterConfig
from .services import send_email
from . import claude_service
from .api_utils import APIResponse, InputValidator, require_json
from app.tasks import generate_newsletter_async, send_email_async

bp = Blueprint("routes", __name__)


@bp.route("/")
def index():
    """Serve the SPA index page."""
    return send_from_directory(current_app.static_folder, "index.html")


@bp.route("/api/send-newsletter", methods=["POST"])
@require_json
def send_newsletter():
    """Send newsletter email to recipient."""
    import markdown
    from app.email_templates import get_newsletter_template
    
    data = request.json
    to_email = InputValidator.sanitize_string(data.get('to_email', ''))
    subject = data.get('subject', '')
    content = data.get('content', '')
    
    if not to_email or '@' not in to_email:
        return APIResponse.error("Valid email address required")
    
    if not subject or not content:
        return APIResponse.error("Subject and content are required")
    
    # Convert markdown-style content to HTML
    html_content = markdown.markdown(
        content,
        extensions=['nl2br', 'sane_lists']  # Preserve line breaks and better list handling
    )
    
    # Wrap in newsletter template
    full_html = get_newsletter_template(
        subject=subject,
        content=html_content,
        preheader=subject[:100]  # Use first 100 chars of subject as preheader
    )
    
    # Queue the email task
    task = send_email_async.delay(
        to_email,
        subject,
        full_html
    )
    
    return APIResponse.processing(
        task_id=task.id,
        message=f"Sending newsletter to '{to_email}'"
    )


@bp.route("/api/newsletters", methods=["GET"])
def get_newsletters():
    """Get all newsletters for the current user."""
    from flask_login import current_user
    from .auth_routes import get_db_session
    from .models import Newsletter
    import os
    
    db = get_db_session()
    
    # In development/testing mode, show all newsletters if not authenticated
    is_dev_mode = os.getenv('FLASK_ENV') == 'development'
    
    if not current_user.is_authenticated:
        if is_dev_mode:
            # Show all newsletters from all users for testing
            newsletters = db.query(Newsletter).all()
            return jsonify({
                'success': True,
                'newsletters': [{
                    'id': nl.id,
                    'name': nl.name,
                    'topic': nl.topic,
                    'schedule': nl.schedule,
                    'last_sent_at': nl.last_sent_at.isoformat() if nl.last_sent_at else None,
                    'created_at': nl.created_at.isoformat() if nl.created_at else None,
                    'issue_count': len(nl.issues)
                } for nl in newsletters],
                'authenticated': False,
                'dev_mode': True
            })
        else:
            return jsonify({
                'success': True,
                'newsletters': [],
                'authenticated': False
            })
    
    # Authenticated user - show only their newsletters
    newsletters = db.query(Newsletter).filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'success': True,
        'authenticated': True,
        'newsletters': [{
            'id': nl.id,
            'name': nl.name,
            'topic': nl.topic,
            'schedule': nl.schedule,
            'last_sent_at': nl.last_sent_at.isoformat() if nl.last_sent_at else None,
            'created_at': nl.created_at.isoformat() if nl.created_at else None,
            'issue_count': len(nl.issues)
        } for nl in newsletters]
    })


@bp.route("/api/newsletters", methods=["POST"])
@require_json
def create_newsletter():
    """Create a new newsletter."""
    from flask_login import current_user
    from .auth_routes import get_db_session
    from .models import Newsletter, User
    import os
    
    is_dev_mode = os.getenv('FLASK_ENV') == 'development'
    
    # In dev mode, create newsletters for a test user if not authenticated
    if not current_user.is_authenticated:
        if not is_dev_mode:
            return APIResponse.error("Authentication required", status_code=401)
        
        # Get or create a test user
        db = get_db_session()
        test_user = db.query(User).filter_by(email='test@thinkwrapper.local').first()
        if not test_user:
            test_user = User(
                email='test@thinkwrapper.local',
                name='Test User',
                oauth_provider='local',
                is_active=True
            )
            db.add(test_user)
            db.commit()
        user_id = test_user.id
    else:
        user_id = current_user.id
    
    data = request.json
    name = InputValidator.sanitize_string(data.get('name', ''))
    topic = InputValidator.sanitize_string(data.get('topic', ''))
    schedule = data.get('schedule', 'weekly')
    
    # Validate inputs
    if not name or len(name) < 3:
        return APIResponse.error("Newsletter name must be at least 3 characters")
    
    is_valid, error_msg = InputValidator.validate_topic(topic)
    if not is_valid:
        return APIResponse.error(error_msg)
    
    # Create newsletter in database
    db = get_db_session()
    newsletter = Newsletter(
        user_id=user_id,
        name=name,
        topic=topic,
        schedule=schedule
    )
    db.add(newsletter)
    db.commit()
    
    return jsonify({
        'success': True,
        'message': 'Newsletter created successfully',
        'newsletter': {
            'id': newsletter.id,
            'name': newsletter.name,
            'topic': newsletter.topic,
            'schedule': newsletter.schedule,
            'created_at': newsletter.created_at.isoformat()
        }
    }), 201


@bp.route("/api/newsletters/<int:newsletter_id>", methods=["GET"])
def get_newsletter(newsletter_id):
    """Get a specific newsletter by ID."""
    from flask_login import current_user
    from .auth_routes import get_db_session
    from .models import Newsletter
    import os
    
    db = get_db_session()
    newsletter = db.query(Newsletter).filter_by(id=newsletter_id).first()
    
    if not newsletter:
        return APIResponse.error("Newsletter not found", status_code=404)
    
    # Check authorization (unless dev mode)
    is_dev_mode = os.getenv('FLASK_ENV') == 'development'
    if not is_dev_mode:
        if not current_user.is_authenticated or newsletter.user_id != current_user.id:
            return APIResponse.error("Unauthorized", status_code=403)
    
    return jsonify({
        'success': True,
        'newsletter': {
            'id': newsletter.id,
            'name': newsletter.name,
            'topic': newsletter.topic,
            'schedule': newsletter.schedule,
            'style': 'professional',  # Default for now
            'last_sent_at': newsletter.last_sent_at.isoformat() if newsletter.last_sent_at else None,
            'created_at': newsletter.created_at.isoformat() if newsletter.created_at else None,
            'issue_count': len(newsletter.issues)
        }
    })


@bp.route("/api/newsletters/<int:newsletter_id>", methods=["PUT"])
@require_json
def update_newsletter(newsletter_id):
    """Update a specific newsletter."""
    from flask_login import current_user
    from .auth_routes import get_db_session
    from .models import Newsletter
    import os
    
    db = get_db_session()
    newsletter = db.query(Newsletter).filter_by(id=newsletter_id).first()
    
    if not newsletter:
        return APIResponse.error("Newsletter not found", status_code=404)
    
    # Check authorization (unless dev mode)
    is_dev_mode = os.getenv('FLASK_ENV') == 'development'
    if not is_dev_mode:
        if not current_user.is_authenticated or newsletter.user_id != current_user.id:
            return APIResponse.error("Unauthorized", status_code=403)
    
    # Update fields
    data = request.json
    if 'name' in data:
        newsletter.name = InputValidator.sanitize_string(data['name'])
    if 'topic' in data:
        newsletter.topic = InputValidator.sanitize_string(data['topic'])
    if 'schedule' in data:
        schedule = data['schedule']
        if schedule not in ['daily', 'weekly', 'biweekly', 'monthly']:
            return APIResponse.error("Invalid schedule")
        newsletter.schedule = schedule
    
    db.commit()
    
    return jsonify({
        'success': True,
        'message': 'Newsletter updated successfully',
        'newsletter': {
            'id': newsletter.id,
            'name': newsletter.name,
            'topic': newsletter.topic,
            'schedule': newsletter.schedule,
            'updated_at': datetime.now().isoformat()
        }
    })


@bp.route("/api/generate", methods=["POST"])
@require_json
def generate_newsletter():
    """Generate a newsletter based on the provided topic."""
    data = request.json
    topic = InputValidator.sanitize_string(data.get('topic', ''))
    style = data.get('style', 'concise')
    schedule = data.get('schedule', 'weekly')  # For date filtering
    newsletter_id = data.get('newsletter_id')

    # Validate topic
    is_valid, error_msg = InputValidator.validate_topic(topic)
    if not is_valid:
        return APIResponse.error(error_msg)

    # Validate style
    is_valid, error_msg = InputValidator.validate_style(style)
    if not is_valid:
        return APIResponse.error(error_msg)

    # Prevent duplicate generation for the same newsletter.
    # This is critical because duplicate frontend requests (double-clicks, re-mounts,
    # retries) can enqueue multiple Celery tasks which then run in parallel and
    # blow through Brave rate limits.
    if newsletter_id is not None:
        from app.celery_config import celery

        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.Redis.from_url(redis_url, decode_responses=True)
        dedupe_key = f"thinkwrapper:generate_newsletter:{newsletter_id}"

        existing_task_id = r.get(dedupe_key)
        if existing_task_id:
            existing_state = celery.AsyncResult(existing_task_id).state
            if existing_state not in ('SUCCESS', 'FAILURE', 'REVOKED'):
                return APIResponse.processing(
                    task_id=existing_task_id,
                    message=f"Newsletter generation already in progress for '{topic}'"
                )
            # Terminal state: clear key so a new run can be started.
            r.delete(dedupe_key)

        # Reserve the slot atomically and use the reserved id as the Celery task_id.
        task_id = str(uuid.uuid4())
        reserved = r.set(dedupe_key, task_id, nx=True, ex=60 * 30)  # 30 minutes
        if not reserved:
            # Someone else reserved it just now; return that task.
            concurrent_task_id = r.get(dedupe_key)
            if concurrent_task_id:
                return APIResponse.processing(
                    task_id=concurrent_task_id,
                    message=f"Newsletter generation already in progress for '{topic}'"
                )

        task = generate_newsletter_async.apply_async(args=[topic, style, schedule], task_id=task_id)
    else:
        # Fallback: no newsletter_id provided; queue normally.
        task = generate_newsletter_async.delay(topic, style, schedule)

    return APIResponse.processing(
        task_id=task.id,
        message=f"Generating newsletter about '{topic}'"
    )


@bp.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get the status of a Celery task with progress tracking."""
    from app.celery_config import celery
    task = celery.AsyncResult(task_id)

    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is waiting to be processed'
        }
    elif task.state == 'PROGRESS':
        # Return progress information
        response = {
            'state': task.state,
            'progress': task.info  # Contains stage, message, percent
        }
    elif task.state == 'FAILURE':
        response = {
            'state': task.state,
            'status': str(task.info),
        }
    else:
        response = {
            'state': task.state,
            'result': task.result if task.state == 'SUCCESS' else None
        }

    return jsonify(response)


@bp.route('/api/admin/synthesize', methods=['POST'])
@require_json
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

    newsletter_id = data.get('newsletter_id')
    topic = InputValidator.sanitize_string(data.get('topic', ''))

    if not newsletter_id:
        return APIResponse.error('newsletter_id is required')

    # Validate topic
    is_valid, error_msg = InputValidator.validate_topic(topic)
    if not is_valid:
        return APIResponse.error(error_msg)

    # Optional parameters
    style = data.get('style', 'professional')
    output_format = data.get('format', 'html')
    send_email_flag = data.get('send_email', False)
    email_to = data.get('email_to')

    # Validate style
    is_valid, error_msg = InputValidator.validate_style(style)
    if not is_valid:
        return APIResponse.error(error_msg)

    # Validate format
    is_valid, error_msg = InputValidator.validate_format(output_format)
    if not is_valid:
        return APIResponse.error(error_msg)

    # Validate send_email requirements
    if send_email_flag:
        is_valid, error_msg = InputValidator.validate_email(email_to)
        if not is_valid:
            return APIResponse.error(error_msg)

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
            return APIResponse.error(
                'Newsletter synthesis failed',
                details=result.get('error'),
                status_code=500
            )

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

        return APIResponse.success(data={
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
        })

    except Exception as e:
        current_app.logger.error(f"Newsletter synthesis error: {str(e)}")
        return APIResponse.error(
            'Internal server error',
            details=str(e),
            status_code=500
        )


@bp.route('/api/admin/newsletter/config', methods=['GET', 'POST'])
def newsletter_config():
    """
    Get or update newsletter configuration settings.

    GET: Returns current configuration
    POST: Updates configuration with provided settings
    """
    config = NewsletterConfig()

    if request.method == 'GET':
        return APIResponse.success(data=config.to_dict())

    # POST - update configuration
    if not request.is_json or not request.json:
        return APIResponse.error('No configuration data provided')

    data = request.json

    try:
        config.from_dict(data)
        is_valid, error_message = config.validate()

        if not is_valid:
            return APIResponse.error(error_message)

        # In a real implementation, save config to database
        return APIResponse.success(data={'config': config.to_dict()})

    except Exception as e:
        return APIResponse.error(
            'Failed to update configuration',
            details=str(e),
            status_code=500
        )


@bp.route('/api/admin/newsletter/preview', methods=['POST'])
@require_json
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

    subject = InputValidator.sanitize_string(data.get('subject', ''))
    content = InputValidator.sanitize_string(data.get('content', ''))
    output_format = data.get('format', 'html')

    if not subject:
        return APIResponse.error('subject is required')
    if not content:
        return APIResponse.error('content is required')

    # Validate format
    is_valid, error_msg = InputValidator.validate_format(output_format)
    if not is_valid:
        return APIResponse.error(error_msg)

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

        return APIResponse.success(data={'rendered': rendered_output})

    except Exception as e:
        return APIResponse.error(
            'Preview generation failed',
            details=str(e),
            status_code=500
        )


@bp.route('/api/claude/generate', methods=['POST'])
@require_json
def claude_generate():
    """
    Generate text using Claude API (demo endpoint).

    Request body:
        {
            "prompt": "Your prompt text",
            "model": "claude-haiku-4-5" (optional),
            "max_tokens": 1024 (optional),
            "temperature": 1.0 (optional),
            "system_prompt": "System prompt" (optional)
        }

    Response:
        {
            "success": true,
            "text": "Generated text...",
            "model": "claude-haiku-4-5",
            "usage": {"input_tokens": 10, "output_tokens": 100}
        }
    """
    data = request.json

    prompt = InputValidator.sanitize_string(data.get('prompt', ''))
    if not prompt:
        return APIResponse.error('No prompt provided')

    # Optional parameters
    model = data.get('model', 'claude-haiku-4-5')
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
        return APIResponse.error(
            'Failed to generate text. Check API key configuration.',
            status_code=500
        )

    return APIResponse.success(data={
        'text': result['text'],
        'model': result['model'],
        'usage': result['usage'],
        'stop_reason': result['stop_reason']
    })

@bp.route('/api/claude/newsletter', methods=['POST'])
@require_json
def claude_newsletter():
    """
    Generate newsletter content using Claude API with Brave Search integration.

    Request body:
        {
            "topic": "Newsletter topic",
            "style": "professional" (optional),
            "max_tokens": 2000 (optional),
            "search_count": 10 (optional),
            "use_search": true (optional, defaults to true for real URLs)
        }

    Response:
        {
            "success": true,
            "subject": "Newsletter subject",
            "content": "Newsletter body...",
            "articles": [{"title": "...", "url": "...", "description": "..."}],
            "search_source": "brave" or "mock",
            "model": "claude-haiku-4-5",
            "usage": {"input_tokens": 50, "output_tokens": 500}
        }
    """
    data = request.json

    topic = InputValidator.sanitize_string(data.get('topic', ''))

    # Validate topic
    is_valid, error_msg = InputValidator.validate_topic(topic)
    if not is_valid:
        return APIResponse.error(error_msg)

    # Optional parameters
    style = data.get('style', 'professional')
    max_tokens = data.get('max_tokens', 2000)
    search_count = data.get('search_count', 10)
    use_search = data.get('use_search', True)

    # Validate style
    is_valid, error_msg = InputValidator.validate_style(style)
    if not is_valid:
        return APIResponse.error(error_msg)

    # Generate newsletter using Claude with Brave Search integration
    if use_search:
        result = claude_service.generate_newsletter_with_search(
            topic=topic,
            style=style,
            max_tokens=max_tokens,
            search_count=search_count
        )
    else:
        # Fallback to old method without search (for backwards compatibility)
        result = claude_service.generate_newsletter_content_claude(
            topic=topic,
            style=style,
            max_tokens=max_tokens
        )

    if result is None:
        return APIResponse.error(
            'Failed to generate newsletter. Check API key configuration.',
            status_code=500
        )

    # Build response data
    response_data = {
        'subject': result['subject'],
        'content': result['content'],
        'model': result['model'],
        'usage': result['usage']
    }
    
    # Add search-specific fields if available
    if 'articles' in result:
        response_data['articles'] = result['articles']
        response_data['search_source'] = result['search_source']
        response_data['total_articles'] = result['total_articles']

    return APIResponse.success(data=response_data)


@bp.route('/api/payment/checkout', methods=['POST'])
@require_json
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

    price_id = data.get('price_id')
    customer_email = data.get('customer_email')
    success_url = data.get('success_url')
    cancel_url = data.get('cancel_url')
    metadata = data.get('metadata', {})

    if not price_id:
        return APIResponse.error('price_id is required')

    # Validate email
    is_valid, error_msg = InputValidator.validate_email(customer_email)
    if not is_valid:
        return APIResponse.error(error_msg)

    if not success_url:
        return APIResponse.error('success_url is required')

    paddle_service = get_paddle_service()
    checkout_session = paddle_service.create_checkout_session(
        price_id=price_id,
        customer_email=customer_email,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata
    )

    if checkout_session:
        return APIResponse.success(data={
            'checkout_url': checkout_session.get('data', {}).get('url'),
            'session_id': checkout_session.get('data', {}).get('id')
        })
    else:
        return APIResponse.error(
            'Failed to create checkout session',
            status_code=500
        )

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
        return APIResponse.error('Missing signature')

    # Verify webhook signature
    paddle_service = get_paddle_service()
    if not paddle_service.verify_webhook_signature(payload, signature):
        current_app.logger.error("Invalid webhook signature")
        return APIResponse.error('Invalid signature', status_code=401)

    # Parse webhook data
    try:
        webhook_data = request.json
        if not webhook_data:
            return APIResponse.error('No webhook data provided')

        event_type = webhook_data.get('event_type')
        event_data = webhook_data.get('data', {})

        if not event_type:
            return APIResponse.error('Missing event_type')

        # Process the webhook event
        result = paddle_service.process_webhook_event(event_type, event_data)

        current_app.logger.info(
            f"Webhook processed: {event_type} - Result: {result.get('status')}"
        )

        return APIResponse.success(data={
            'status': 'received',
            'event_type': event_type
        })

    except Exception as e:
        current_app.logger.error(f"Webhook processing error: {str(e)}")
        return APIResponse.error(
            'Webhook processing failed',
            status_code=500
        )

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

    if not subscription_id:
        return APIResponse.error('subscription_id is required')

    data = request.json or {}
    effective_date = data.get('effective_date')

    paddle_service = get_paddle_service()
    success = paddle_service.cancel_subscription(
        subscription_id=subscription_id,
        effective_date=effective_date
    )

    if success:
        return APIResponse.success(message='Subscription cancelled')
    else:
        return APIResponse.error(
            'Failed to cancel subscription',
            status_code=500
        )

# Catch-all to support client-side routing
@bp.route("/<path:path>")
def catch_all(path):
    """Serve static files or return index.html for client-side routing."""
    try:
        return send_from_directory(current_app.static_folder, path)
    except Exception:
        return send_from_directory(current_app.static_folder, "index.html")
