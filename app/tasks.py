"""Celery tasks for background processing."""
import logging
from datetime import datetime, timedelta, timezone
from celery import Task
from celery.exceptions import MaxRetriesExceededError
from app.celery_config import celery
from app import services

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with error handling and logging."""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Success handler."""
        logger.info(f"Task {self.name}[{task_id}] succeeded with result: {retval}")
        return super().on_success(retval, task_id, args, kwargs)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Failure handler."""
        logger.error(f"Task {self.name}[{task_id}] failed: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Retry handler."""
        logger.warning(f"Task {self.name}[{task_id}] retrying: {exc}")
        return super().on_retry(exc, task_id, args, kwargs, einfo)


@celery.task(base=CallbackTask, bind=True, max_retries=3, default_retry_delay=60)
def generate_newsletter_async(self, topic, style="concise"):
    """
    Generate newsletter content asynchronously.
    
    Args:
        topic (str): The subject of the newsletter
        style (str): Style descriptor for the content
        
    Returns:
        dict: Generated content with subject and body
    """
    try:
        logger.info(f"Starting newsletter generation for topic: {topic}")
        result = services.generate_newsletter_content(topic, style)
        
        if result is None:
            error_msg = (
                f"Newsletter generation service returned None for topic '{topic}' - "
                "check OpenAI service configuration, API key validity, and API availability"
            )
            raise Exception(error_msg)
        
        logger.info(f"Successfully generated newsletter for topic: {topic}")
        return result
    except Exception as exc:
        logger.error(f"Error generating newsletter: {exc}")
        try:
            # Retry with exponential backoff
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for newsletter generation: {topic}")
            return {"error": "Failed to generate newsletter after multiple retries"}


@celery.task(base=CallbackTask, bind=True, max_retries=5, default_retry_delay=30)
def send_email_async(self, to_email, subject, content):
    """
    Send email asynchronously using SendGrid.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject line
        content (str): HTML content of the email
        
    Returns:
        dict: Success status and details
    """
    try:
        logger.info(f"Sending email to {to_email} with subject: {subject}")
        success = services.send_email(to_email, subject, content)
        
        if not success:
            error_msg = (
                f"Email sending failed for recipient '{to_email}' with subject '{subject}' - "
                "check SendGrid service configuration, API key validity, and service availability"
            )
            raise Exception(error_msg)
        
        logger.info(f"Successfully sent email to {to_email}")
        return {
            "success": True,
            "to_email": to_email,
            "subject": subject,
            "sent_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as exc:
        logger.error(f"Error sending email to {to_email}: {exc}")
        try:
            # Retry with exponential backoff
            raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for email to: {to_email}")
            return {
                "success": False,
                "error": "Failed to send email after multiple retries",
                "to_email": to_email
            }


@celery.task(base=CallbackTask, bind=True, max_retries=3)
def send_newsletter_issue(self, newsletter_id, recipient_email):
    """
    Generate and send a newsletter issue.
    
    This is a combined task that generates content and sends email.
    Uses task chaining to avoid blocking calls.
    
    Args:
        newsletter_id (int): ID of the newsletter
        recipient_email (str): Email address to send to
        
    Returns:
        dict: Result with generation and sending status
    """
    try:
        logger.info(f"Processing newsletter issue {newsletter_id} for {recipient_email}")
        
        # In a real implementation, fetch newsletter details from database
        # For now, use a placeholder topic
        topic = f"Newsletter {newsletter_id} Update"
        
        # Generate content synchronously (within the task)
        content_result = services.generate_newsletter_content(topic)
        
        if not content_result or "error" in content_result:
            raise Exception(f"Content generation failed: {content_result}")
        
        # Send email synchronously (within the task)
        email_success = services.send_email(
            recipient_email, 
            content_result['subject'], 
            content_result['content']
        )
        
        if not email_success:
            raise Exception(f"Email sending failed for {recipient_email}")
        
        logger.info(f"Successfully sent newsletter {newsletter_id} to {recipient_email}")
        return {
            "success": True,
            "newsletter_id": newsletter_id,
            "recipient": recipient_email,
            "content_generated": True,
            "email_sent": True
        }
    except Exception as exc:
        logger.error(f"Error processing newsletter issue {newsletter_id}: {exc}")
        try:
            raise self.retry(exc=exc, countdown=120)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for newsletter {newsletter_id}")
            return {
                "success": False,
                "error": str(exc),
                "newsletter_id": newsletter_id
            }


@celery.task(base=CallbackTask)
def check_scheduled_newsletters():
    """
    Periodic task to check for scheduled newsletters that need to be sent.
    
    This is an example periodic task that runs every 15 minutes.
    In a production environment, this would query the database for
    newsletters scheduled to be sent.
    
    Returns:
        dict: Summary of newsletters checked and sent
    """
    try:
        logger.info("Checking for scheduled newsletters...")
        
        # Placeholder logic - in real implementation:
        # 1. Query database for newsletters with schedule
        # 2. Check if they're due to be sent
        # 3. Trigger send_newsletter_issue for each due newsletter
        
        checked_count = 0
        sent_count = 0
        
        # Example: Query would look something like this
        # from app.models import Newsletter
        # from sqlalchemy import create_engine
        # from sqlalchemy.orm import sessionmaker
        # 
        # engine = create_engine(os.environ.get('DATABASE_URL'))
        # Session = sessionmaker(bind=engine)
        # session = Session()
        # 
        # now = datetime.utcnow()
        # due_newsletters = session.query(Newsletter).filter(
        #     Newsletter.schedule.isnot(None),
        #     Newsletter.last_sent_at < now - timedelta(days=7)
        # ).all()
        # 
        # for newsletter in due_newsletters:
        #     send_newsletter_issue.delay(newsletter.id, newsletter.user.email)
        #     sent_count += 1
        
        logger.info(f"Newsletter check complete: {checked_count} checked, {sent_count} sent")
        return {
            "success": True,
            "checked": checked_count,
            "sent": sent_count,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as exc:
        logger.error(f"Error checking scheduled newsletters: {exc}")
        return {
            "success": False,
            "error": str(exc)
        }


@celery.task(base=CallbackTask)
def cleanup_old_results():
    """
    Periodic task to clean up old task results from the backend.
    
    This runs daily at 2 AM to prevent result backend from growing indefinitely.
    
    Returns:
        dict: Summary of cleanup operation
    """
    try:
        logger.info("Starting cleanup of old task results...")
        
        # Get task results older than 24 hours
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # In production, you might want to use Celery's result backend inspection
        # or implement custom cleanup based on your storage backend
        
        # For Redis backend, expired results are automatically cleaned up
        # based on result_expires configuration
        
        logger.info("Cleanup complete")
        return {
            "success": True,
            "cleaned_at": datetime.now(timezone.utc).isoformat(),
            "message": "Automatic cleanup via result_expires configuration"
        }
    except Exception as exc:
        logger.error(f"Error during cleanup: {exc}")
        return {
            "success": False,
            "error": str(exc)
        }


@celery.task(base=CallbackTask, bind=True)
def example_notification_task(self, user_id, message):
    """
    Example task for sending notifications.
    
    This demonstrates a simple async task pattern for notifications
    or other quick operations.
    
    Args:
        user_id (int): User ID to notify
        message (str): Notification message
        
    Returns:
        dict: Notification result
    """
    try:
        logger.info(f"Sending notification to user {user_id}: {message}")
        
        # In production, this would:
        # - Store notification in database
        # - Send push notification
        # - Send SMS/email if configured
        # - Update user's notification count
        
        # Simulate processing
        import time
        time.sleep(0.1)
        
        logger.info(f"Notification sent to user {user_id}")
        return {
            "success": True,
            "user_id": user_id,
            "message": message,
            "sent_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as exc:
        logger.error(f"Error sending notification to user {user_id}: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "user_id": user_id
        }


@celery.task(base=CallbackTask, bind=True, max_retries=3)
def example_api_call_task(self, endpoint, method="GET", data=None):
    """
    Example task for making external API calls.
    
    This demonstrates a pattern for async API calls with retries.
    
    Args:
        endpoint (str): API endpoint URL
        method (str): HTTP method
        data (dict): Request data
        
    Returns:
        dict: API response
    """
    try:
        logger.info(f"Making API call to {endpoint}")
        
        # In production, this would use requests or httpx
        # import requests
        # response = requests.request(method, endpoint, json=data, timeout=30)
        # response.raise_for_status()
        # return response.json()
        
        # Placeholder response
        logger.info(f"API call completed for {endpoint}")
        return {
            "success": True,
            "endpoint": endpoint,
            "method": method,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as exc:
        logger.error(f"Error making API call to {endpoint}: {exc}")
        try:
            raise self.retry(exc=exc, countdown=60)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for API call to {endpoint}")
            return {
                "success": False,
                "error": str(exc),
                "endpoint": endpoint
            }
