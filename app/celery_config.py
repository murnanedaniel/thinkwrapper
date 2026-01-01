"""Celery configuration and initialization for ThinkWrapper."""
import os
from celery import Celery
from celery.schedules import crontab


def make_celery(app_name=__name__):
    """
    Create and configure a Celery instance.
    
    Args:
        app_name (str): Name of the application
        
    Returns:
        Celery: Configured Celery instance
    """
    # Get broker and backend URLs from environment
    broker_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    result_backend = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    celery_app = Celery(
        app_name,
        broker=broker_url,
        backend=result_backend,
        include=['app.tasks']
    )
    
    # Celery configuration
    celery_app.conf.update(
        # Task configuration
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        
        # Result backend configuration
        result_expires=3600,  # Results expire after 1 hour
        
        # Worker configuration
        worker_prefetch_multiplier=4,
        worker_max_tasks_per_child=1000,
        
        # Error handling
        task_acks_late=True,  # Acknowledge task after completion
        task_reject_on_worker_lost=True,  # Reject task if worker crashes
        
        # Logging
        worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
        worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
        
        # Beat schedule for periodic tasks
        beat_schedule={
            'check-scheduled-newsletters': {
                'task': 'app.tasks.check_scheduled_newsletters',
                'schedule': crontab(minute='*/15'),  # Every 15 minutes
            },
            'cleanup-old-task-results': {
                'task': 'app.tasks.cleanup_old_results',
                'schedule': crontab(hour='2', minute='0'),  # Daily at 2 AM
            },
        },
    )
    
    return celery_app


# Create the global Celery instance
celery = make_celery()
