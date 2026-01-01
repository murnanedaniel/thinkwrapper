# Setup Celery Task Queue for Async Processing

**Labels**: `feature`, `infrastructure`, `async`, `high-priority`

## Overview
Implement Celery with Redis for asynchronous task processing, enabling background newsletter generation and scheduled deliveries.

## Objectives
- Configure Celery with Redis broker
- Create async tasks for newsletter generation
- Implement scheduled newsletter delivery
- Add task monitoring and error handling
- Ensure tasks work in both development and production

## Technical Requirements

### Celery Setup
- [ ] Install celery and redis (already in requirements.txt)
- [ ] Create celery application instance
- [ ] Configure Redis as broker and result backend
- [ ] Set up Celery beat for scheduled tasks
- [ ] Configure task routes and priorities

### Application Structure

```python
# app/celery_app.py
from celery import Celery
from app import create_app

def make_celery(app):
    """Create Celery instance."""
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

flask_app = create_app()
celery = make_celery(flask_app)
```

### Tasks to Implement

#### 1. Newsletter Generation Task
- [ ] `tasks.generate_newsletter.delay(newsletter_id, topic)`
- [ ] Async execution of Brave Search + Anthropic synthesis
- [ ] Store generated content in database
- [ ] Handle generation failures with retries
- [ ] Set timeout (e.g., 5 minutes max)

#### 2. Email Delivery Task
- [ ] `tasks.send_newsletter.delay(issue_id, recipients)`
- [ ] Batch email sending with rate limiting
- [ ] Track delivery status
- [ ] Retry failed deliveries
- [ ] Handle bounces and failures

#### 3. Scheduled Newsletter Task
- [ ] `tasks.process_scheduled_newsletters.delay()`
- [ ] Check for newsletters due to be sent
- [ ] Generate and send automatically
- [ ] Update last_sent_at timestamp
- [ ] Run periodically via Celery Beat

### Task Configuration
- [ ] Task priorities (high for user-initiated, normal for scheduled)
- [ ] Rate limits (respect API quotas)
- [ ] Retries with exponential backoff
- [ ] Task timeouts
- [ ] Result expiration

### Monitoring & Logging
- [ ] Task status tracking
- [ ] Flower for task monitoring (optional)
- [ ] Error logging and alerting
- [ ] Performance metrics
- [ ] Dead letter queue for failed tasks

### Development Setup
- [ ] Local Redis instance or Docker
- [ ] Celery worker startup script
- [ ] Celery beat startup script
- [ ] Hot reload for development

### Production Configuration
- [ ] Multiple worker processes
- [ ] Separate queues for different task types
- [ ] Worker autoscaling
- [ ] Health checks
- [ ] Graceful shutdown

### Testing
- [ ] Unit tests for task logic
- [ ] Use CELERY_TASK_ALWAYS_EAGER for synchronous testing
- [ ] Test retry behavior
- [ ] Test scheduled task execution
- [ ] Integration tests with real Redis

### Documentation
- [ ] Celery setup guide
- [ ] Task documentation
- [ ] Monitoring guide
- [ ] Troubleshooting common issues

## Example Implementation

```python
# app/tasks.py
from app.celery_app import celery
from app import db
from app.models import Newsletter, Issue
from app.services import synthesize_newsletter, send_email
import logging

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3)
def generate_newsletter_task(self, newsletter_id):
    """
    Asynchronously generate newsletter content.

    Args:
        newsletter_id: ID of newsletter to generate

    Returns:
        issue_id: ID of created issue
    """
    try:
        newsletter = Newsletter.query.get(newsletter_id)
        if not newsletter:
            logger.error(f"Newsletter {newsletter_id} not found")
            return None

        # Generate newsletter (calls Brave + Anthropic)
        result = synthesize_newsletter(
            topic=newsletter.topic,
            search_results=None,  # Will fetch internally
            research_output=None
        )

        # Create issue record
        issue = Issue(
            newsletter_id=newsletter_id,
            subject=result['subject'],
            content=result['content']
        )
        db.session.add(issue)
        db.session.commit()

        logger.info(f"Newsletter generated: issue_id={issue.id}")
        return issue.id

    except Exception as exc:
        logger.error(f"Newsletter generation failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@celery.task(bind=True, max_retries=5)
def send_newsletter_task(self, issue_id, recipient_email):
    """
    Send newsletter to recipient.

    Args:
        issue_id: ID of issue to send
        recipient_email: Email address
    """
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            logger.error(f"Issue {issue_id} not found")
            return False

        # Send email
        success = send_email(
            to_email=recipient_email,
            subject=issue.subject,
            content=issue.content
        )

        if success:
            issue.sent_at = datetime.utcnow()
            db.session.commit()
            logger.info(f"Newsletter sent to {recipient_email}")

        return success

    except Exception as exc:
        logger.error(f"Email delivery failed: {exc}")
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes

@celery.task
def process_scheduled_newsletters():
    """
    Process all newsletters scheduled for delivery.
    Runs periodically via Celery Beat.
    """
    from datetime import datetime, timedelta

    # Find newsletters due for delivery
    now = datetime.utcnow()
    newsletters = Newsletter.query.filter(
        Newsletter.is_active == True,
        Newsletter.schedule.isnot(None)
    ).all()

    for newsletter in newsletters:
        # Check if it's time to send based on schedule
        if should_send_newsletter(newsletter, now):
            # Chain tasks: generate then send
            chain = (
                generate_newsletter_task.s(newsletter.id) |
                send_newsletter_task.s(newsletter.user.email)
            )
            chain.apply_async()

            newsletter.last_sent_at = now
            db.session.commit()

# Configure Celery Beat schedule
celery.conf.beat_schedule = {
    'process-scheduled-newsletters': {
        'task': 'app.tasks.process_scheduled_newsletters',
        'schedule': 3600.0,  # Run every hour
    },
}
```

## Running Celery

### Development
```bash
# Terminal 1: Celery worker
celery -A app.celery_app worker --loglevel=info

# Terminal 2: Celery beat (for scheduled tasks)
celery -A app.celery_app beat --loglevel=info
```

### Production (Render)
Already configured in `render.yaml`:
```yaml
- type: worker
  name: thinkwrapper-worker
  startCommand: celery -A app.celery_app worker --loglevel=info
```

## Acceptance Criteria
- [ ] Celery configured and running
- [ ] Newsletter generation runs asynchronously
- [ ] Email delivery runs in background
- [ ] Scheduled newsletters processed automatically
- [ ] Failed tasks retry appropriately
- [ ] Tests achieve >80% coverage
- [ ] Monitoring/logging in place
- [ ] Documentation complete
- [ ] Works in both development and production

## Related Issues
- Depends on: #01 (Anthropic API), #03 (Newsletter Synthesis)
- Blocks: Scheduled newsletter features

## Estimated Effort
Medium (2-3 days)

## Resources
- [Celery Documentation](https://docs.celeryproject.org/)
- [Flask + Celery Guide](https://flask.palletsprojects.com/en/2.3.x/patterns/celery/)
- [Redis Documentation](https://redis.io/docs/)
