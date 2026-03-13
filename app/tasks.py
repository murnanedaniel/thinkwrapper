"""Celery tasks for background processing."""
import os
import logging
from datetime import datetime, timedelta, timezone
from celery import Task
from celery.exceptions import MaxRetriesExceededError
from app.celery_config import celery

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {self.name}[{task_id}] succeeded")
        return super().on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {self.name}[{task_id}] failed: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)


def _get_db_session():
    """Get a database session for use in Celery tasks."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    database_url = os.environ.get('DATABASE_URL', 'sqlite:///thinkwrapper.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()


@celery.task(base=CallbackTask, bind=True, max_retries=3, default_retry_delay=60)
def generate_newsletter_async(self, topic, style="concise", schedule="weekly", debug_mode=False):
    """Generate newsletter content asynchronously using Claude Agent SDK."""
    try:
        logger.info(f"Starting newsletter generation for topic: {topic}")

        def progress_callback(message):
            self.update_state(state='PROGRESS', meta={'status': str(message)})
            logger.info(f"[Progress] {message}")

        from app.agent_service import generate_newsletter_sync
        result = generate_newsletter_sync(
            topic=topic, schedule=schedule, style=style,
            debug_mode=debug_mode, progress_callback=progress_callback
        )
        if result is None:
            raise Exception(f"Newsletter generation failed for topic '{topic}'")

        logger.info(f"Successfully generated newsletter for topic: {topic}")
        return {'subject': result['subject'], 'content': result['content']}
    except Exception as exc:
        logger.error(f"Error generating newsletter: {exc}")
        try:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        except MaxRetriesExceededError:
            return {"error": "Failed to generate newsletter after multiple retries"}


@celery.task(base=CallbackTask, bind=True, max_retries=5, default_retry_delay=30)
def send_email_async(self, to_email, subject, content):
    """Send email asynchronously using Mailjet."""
    try:
        from app.services import send_email
        logger.info(f"Sending email to {to_email}")
        success = send_email(to_email, subject, content)
        if not success:
            raise Exception(f"Email sending failed for {to_email}")
        return {"success": True, "to_email": to_email, "sent_at": datetime.now(timezone.utc).isoformat()}
    except Exception as exc:
        logger.error(f"Error sending email: {exc}")
        try:
            raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
        except MaxRetriesExceededError:
            return {"success": False, "error": str(exc)}


@celery.task(base=CallbackTask, bind=True, max_retries=3)
def send_newsletter_issue(self, newsletter_id, recipient_email):
    """Generate and send a newsletter issue. Reads real data from DB."""
    try:
        from app.models import Newsletter, Issue
        from app.newsletter_synthesis import NewsletterRenderer
        from app.services import send_email

        db = _get_db_session()
        newsletter = db.query(Newsletter).get(newsletter_id)
        if not newsletter:
            raise Exception(f"Newsletter {newsletter_id} not found")

        full_topic = newsletter.topic
        if newsletter.description:
            full_topic = f"{newsletter.topic}. Focus on: {newsletter.description}"

        from app.agent_service import generate_newsletter_sync
        result = generate_newsletter_sync(
            topic=full_topic, schedule=newsletter.schedule or 'weekly',
            style=newsletter.style or 'professional'
        )
        if result is None:
            raise Exception(f"Content generation failed for newsletter {newsletter_id}")

        issue = Issue(
            newsletter_id=newsletter.id,
            subject=result['subject'],
            content=result['content'],
        )
        db.add(issue)

        renderer = NewsletterRenderer()
        html_content = renderer.render_html({
            'subject': result['subject'], 'content': result['content']
        })
        email_success = send_email(recipient_email, result['subject'], html_content)

        if email_success:
            issue.sent_at = datetime.utcnow()
            newsletter.last_sent_at = datetime.utcnow()

        db.commit()
        db.close()

        logger.info(f"Newsletter {newsletter_id} issue sent to {recipient_email}")
        return {"success": True, "newsletter_id": newsletter_id, "email_sent": email_success}

    except Exception as exc:
        logger.error(f"Error processing newsletter {newsletter_id}: {exc}")
        try:
            raise self.retry(exc=exc, countdown=120)
        except MaxRetriesExceededError:
            return {"success": False, "error": str(exc)}


SCHEDULE_INTERVALS = {
    'daily': timedelta(days=1),
    'weekly': timedelta(weeks=1),
    'biweekly': timedelta(weeks=2),
    'monthly': timedelta(days=30),
}


@celery.task(base=CallbackTask)
def check_scheduled_newsletters():
    """Check for newsletters due to be sent and trigger sending."""
    try:
        from app.models import Newsletter

        db = _get_db_session()
        now = datetime.utcnow()
        sent_count = 0

        newsletters = db.query(Newsletter).filter(
            Newsletter.status == 'active',
            Newsletter.schedule.isnot(None),
        ).all()

        for newsletter in newsletters:
            interval = SCHEDULE_INTERVALS.get(newsletter.schedule)
            if not interval:
                continue

            if newsletter.last_sent_at is None or (now - newsletter.last_sent_at) >= interval:
                user = newsletter.user
                if user and user.subscription_status == 'active':
                    send_newsletter_issue.delay(newsletter.id, user.email)
                    sent_count += 1
                    logger.info(f"Queued newsletter {newsletter.id} for {user.email}")

        db.close()
        logger.info(f"Newsletter check complete: {len(newsletters)} checked, {sent_count} queued")
        return {"success": True, "checked": len(newsletters), "sent": sent_count}

    except Exception as exc:
        logger.error(f"Error checking scheduled newsletters: {exc}")
        return {"success": False, "error": str(exc)}


@celery.task(base=CallbackTask)
def cleanup_old_results():
    """Periodic cleanup task."""
    logger.info("Cleanup complete (Redis result_expires handles this automatically)")
    return {"success": True, "cleaned_at": datetime.now(timezone.utc).isoformat()}
