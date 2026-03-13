import os

from flask import (
    Blueprint, jsonify, request, current_app, send_from_directory,
)
from datetime import datetime
from functools import wraps
from flask_login import current_user, login_required

from .newsletter_synthesis import NewsletterRenderer
from .services import send_email
from . import claude_service
from .api_utils import APIResponse, InputValidator, require_json
from .models import Newsletter, Issue, User

bp = Blueprint("routes", __name__)


# --- Auth decorators ---

def login_required_api(f):
    """Return 401 JSON instead of redirect for unauthenticated API calls."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return APIResponse.error('Authentication required', status_code=401)
        return f(*args, **kwargs)
    return decorated


def subscription_required(f):
    """Require an active subscription."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return APIResponse.error('Authentication required', status_code=401)
        if current_user.subscription_status != 'active':
            return APIResponse.error('Active subscription required', status_code=403)
        return f(*args, **kwargs)
    return decorated


def get_db():
    return current_app.db_session_factory()


# --- Static file serving ---

@bp.route("/")
def index():
    return send_from_directory(current_app.static_folder, "index.html")


# --- Newsletter Preview (NO auth required - this is the hook) ---

@bp.route('/api/newsletter/preview', methods=['POST'])
@require_json
def preview_newsletter_generate():
    """
    Start async newsletter preview generation. No auth required.
    Returns a task_id — poll /api/task/<task_id> for progress and result.
    """
    data = request.json
    topic = InputValidator.sanitize_string(data.get('topic', ''))
    description = data.get('description', '')
    style = data.get('style', 'professional')

    is_valid, error_msg = InputValidator.validate_topic(topic)
    if not is_valid:
        return APIResponse.error(error_msg)

    is_valid, error_msg = InputValidator.validate_style(style)
    if not is_valid:
        return APIResponse.error(error_msg)

    full_topic = topic
    if description:
        full_topic = f"{topic}. Focus on: {description}"

    from app.tasks import generate_newsletter_async
    task = generate_newsletter_async.delay(full_topic, style, 'weekly')

    return APIResponse.success(data={'task_id': task.id})


# --- Newsletter CRUD (auth + subscription required) ---

@bp.route('/api/newsletters', methods=['GET'])
@login_required_api
def list_newsletters():
    """List current user's newsletters."""
    db = get_db()
    newsletters = db.query(Newsletter).filter_by(user_id=current_user.id).order_by(Newsletter.created_at.desc()).all()

    return APIResponse.success(data=[
        {
            'id': nl.id,
            'name': nl.name,
            'topic': nl.topic,
            'description': nl.description,
            'style': nl.style,
            'status': nl.status,
            'schedule': nl.schedule,
            'last_sent_at': nl.last_sent_at.isoformat() if nl.last_sent_at else None,
            'created_at': nl.created_at.isoformat() if nl.created_at else None,
            'issue_count': len(nl.issues),
        }
        for nl in newsletters
    ])


@bp.route('/api/newsletters', methods=['POST'])
@subscription_required
@require_json
def create_newsletter():
    """
    Create a newsletter and its first issue, then send it.
    Called after payment is confirmed.
    """
    data = request.json
    topic = InputValidator.sanitize_string(data.get('topic', ''))
    name = InputValidator.sanitize_string(data.get('name', ''))
    description = data.get('description', '')
    style = data.get('style', 'professional')
    schedule = data.get('schedule', 'weekly')
    subject = data.get('subject', '')
    content = data.get('content', '')

    is_valid, error_msg = InputValidator.validate_topic(topic)
    if not is_valid:
        return APIResponse.error(error_msg)

    if not name:
        name = topic[:100]
    if not subject or not content:
        return APIResponse.error('subject and content are required (from preview)')

    db = get_db()

    # Create newsletter
    newsletter = Newsletter(
        user_id=current_user.id,
        name=name,
        topic=topic,
        description=description,
        style=style,
        schedule=schedule,
        status='active',
    )
    db.add(newsletter)
    db.flush()

    # Create first issue
    issue = Issue(
        newsletter_id=newsletter.id,
        subject=subject,
        content=content,
    )
    db.add(issue)
    db.commit()

    # Send the first issue immediately
    renderer = NewsletterRenderer()
    html_content = renderer.render_html({'subject': subject, 'content': content})

    email_sent = send_email(current_user.email, subject, html_content)
    if email_sent:
        issue.sent_at = datetime.utcnow()
        newsletter.last_sent_at = datetime.utcnow()
        db.commit()

    return APIResponse.success(data={
        'newsletter_id': newsletter.id,
        'issue_id': issue.id,
        'email_sent': email_sent,
    })


# --- Existing generation endpoints (kept for API compatibility) ---

@bp.route("/api/generate", methods=["POST"])
@require_json
def generate_newsletter():
    """Generate a newsletter (async via Celery)."""
    from app.tasks import generate_newsletter_async
    data = request.json
    topic = InputValidator.sanitize_string(data.get('topic', ''))
    style = data.get('style', 'concise')

    is_valid, error_msg = InputValidator.validate_topic(topic)
    if not is_valid:
        return APIResponse.error(error_msg)
    is_valid, error_msg = InputValidator.validate_style(style)
    if not is_valid:
        return APIResponse.error(error_msg)

    task = generate_newsletter_async.delay(topic, style)
    return APIResponse.processing(
        task_id=task.id,
        message=f"Generating newsletter about '{topic}'"
    )


@bp.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    from app.celery_config import celery
    task = celery.AsyncResult(task_id)

    if task.state == 'PENDING':
        return jsonify({'state': 'PENDING', 'status': 'Waiting to start...'})
    elif task.state == 'PROGRESS':
        return jsonify({'state': 'PROGRESS', 'status': task.info.get('status', '')})
    elif task.state == 'FAILURE':
        return jsonify({'state': 'FAILURE', 'status': str(task.info)})
    elif task.state == 'SUCCESS':
        result = task.result or {}
        # Render HTML preview from the completed task result
        renderer = NewsletterRenderer()
        html_preview = renderer.render_html({
            'subject': result.get('subject', ''),
            'content': result.get('content', '')
        })
        return jsonify({
            'state': 'SUCCESS',
            'result': {
                'subject': result.get('subject', ''),
                'content': result.get('content', ''),
                'html_preview': html_preview,
                'articles': result.get('articles', []),
                'search_source': 'agent',
            }
        })
    else:
        return jsonify({'state': task.state, 'status': str(task.info)})


@bp.route('/api/claude/newsletter', methods=['POST'])
@require_json
def claude_newsletter():
    """Generate newsletter content using Claude API with Brave Search."""
    data = request.json
    topic = InputValidator.sanitize_string(data.get('topic', ''))
    is_valid, error_msg = InputValidator.validate_topic(topic)
    if not is_valid:
        return APIResponse.error(error_msg)

    style = data.get('style', 'professional')
    max_tokens = data.get('max_tokens', 2000)
    search_count = data.get('search_count', 10)
    use_search = data.get('use_search', True)

    is_valid, error_msg = InputValidator.validate_style(style)
    if not is_valid:
        return APIResponse.error(error_msg)

    if use_search:
        result = claude_service.generate_newsletter_with_search(
            topic=topic, style=style, max_tokens=max_tokens, search_count=search_count
        )
    else:
        result = claude_service.generate_newsletter_content_claude(
            topic=topic, style=style, max_tokens=max_tokens
        )

    if result is None:
        return APIResponse.error('Failed to generate newsletter.', status_code=500)

    response_data = {
        'subject': result['subject'], 'content': result['content'],
        'model': result['model'], 'usage': result['usage']
    }
    if 'articles' in result:
        response_data['articles'] = result['articles']
        response_data['search_source'] = result['search_source']
        response_data['total_articles'] = result['total_articles']

    return APIResponse.success(data=response_data)


# --- Payment endpoints ---

@bp.route('/api/payment/checkout', methods=['POST'])
@require_json
def create_payment_checkout():
    from .payment_service import get_paddle_service
    data = request.json
    price_id = data.get('price_id')
    customer_email = data.get('customer_email')
    success_url = data.get('success_url')
    cancel_url = data.get('cancel_url')
    metadata = data.get('metadata', {})

    if not price_id:
        return APIResponse.error('price_id is required')
    is_valid, error_msg = InputValidator.validate_email(customer_email)
    if not is_valid:
        return APIResponse.error(error_msg)
    if not success_url:
        return APIResponse.error('success_url is required')

    paddle_service = get_paddle_service()
    checkout_session = paddle_service.create_checkout_session(
        price_id=price_id, customer_email=customer_email,
        success_url=success_url, cancel_url=cancel_url, metadata=metadata
    )

    if checkout_session:
        return APIResponse.success(data={
            'checkout_url': checkout_session.get('data', {}).get('url'),
            'session_id': checkout_session.get('data', {}).get('id')
        })
    return APIResponse.error('Failed to create checkout session', status_code=500)


@bp.route('/api/payment/webhook', methods=['POST'])
def paddle_webhook():
    """Handle Paddle webhook notifications with DB updates."""
    from .payment_service import get_paddle_service

    payload = request.get_data(as_text=True)
    signature = request.headers.get('Paddle-Signature', '')

    if not signature:
        current_app.logger.error("Webhook received without signature")
        return APIResponse.error('Missing signature')

    paddle_service = get_paddle_service()
    if not paddle_service.verify_webhook_signature(payload, signature):
        current_app.logger.error("Invalid webhook signature")
        return APIResponse.error('Invalid signature', status_code=401)

    try:
        webhook_data = request.json
        if not webhook_data:
            return APIResponse.error('No webhook data provided')

        event_type = webhook_data.get('event_type')
        event_data = webhook_data.get('data', {})

        if not event_type:
            return APIResponse.error('Missing event_type')

        result = paddle_service.process_webhook_event(event_type, event_data)

        current_app.logger.info(f"Webhook processed: {event_type} - {result.get('status')}")
        return APIResponse.success(data={'status': 'received', 'event_type': event_type})

    except Exception as e:
        current_app.logger.error(f"Webhook processing error: {str(e)}")
        return APIResponse.error('Webhook processing failed', status_code=500)


@bp.route('/api/payment/activate-by-checkout', methods=['POST'])
def activate_by_checkout():
    """
    Activate a user's subscription based on a completed Paddle checkout event.
    Called from the frontend after checkout.completed fires.
    This is needed because the Paddle webhook may not have reached the server yet.
    """
    if not current_user.is_authenticated:
        return APIResponse.error('Authentication required', status_code=401)

    data = request.json or {}
    transaction_id = data.get('transaction_id')
    customer_id = data.get('customer_id')

    db = get_db()
    from .models import User
    user = db.query(User).filter_by(id=current_user.id).first()
    if not user:
        return APIResponse.error('User not found', status_code=404)

    # Activate the subscription based on the checkout event
    user.subscription_status = 'active'
    if customer_id and not user.paddle_customer_id:
        user.paddle_customer_id = customer_id
    db.commit()

    current_app.logger.info(f"Subscription activated via checkout for {user.email} (txn: {transaction_id})")
    return APIResponse.success(data={'subscription_status': 'active'})


@bp.route('/api/payment/subscription/<subscription_id>/cancel', methods=['POST'])
def cancel_subscription(subscription_id):
    from .payment_service import get_paddle_service
    data = request.json or {}
    paddle_service = get_paddle_service()
    success = paddle_service.cancel_subscription(subscription_id, data.get('effective_date'))
    if success:
        return APIResponse.success(message='Subscription cancelled')
    return APIResponse.error('Failed to cancel subscription', status_code=500)


# --- Config endpoint (for frontend to get Paddle settings) ---

@bp.route('/api/config', methods=['GET'])
def get_frontend_config():
    """Return public configuration for the frontend."""
    return APIResponse.success(data={
        'paddle_client_token': os.environ.get('PADDLE_CLIENT_TOKEN', ''),
        'paddle_price_id': os.environ.get('PADDLE_PRICE_ID', ''),
        'paddle_vendor_id': os.environ.get('PADDLE_VENDOR_ID', ''),
        'paddle_product_id': os.environ.get('PADDLE_PRODUCT_ID', ''),
        'paddle_sandbox': os.environ.get('PADDLE_SANDBOX', 'true').lower() == 'true',
    })


# Catch-all for SPA routing
@bp.route("/<path:path>")
def catch_all(path):
    try:
        return send_from_directory(current_app.static_folder, path)
    except Exception:
        return send_from_directory(current_app.static_folder, "index.html")

