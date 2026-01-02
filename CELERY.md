# Celery Task Queue Setup and Usage

This document provides comprehensive information about the Celery task queue setup in ThinkWrapper for background processing and async workflows.

## Overview

ThinkWrapper uses Celery with Redis as the message broker and result backend to handle asynchronous tasks such as:
- Newsletter content generation
- Email sending via SendGrid
- Scheduled newsletter delivery
- API calls and notifications
- Periodic maintenance tasks

## Architecture

```
Flask App → Celery Tasks → Redis Broker → Celery Workers → Results Backend (Redis)
                                              ↓
                                         Task Execution
```

### Components

1. **Celery Configuration** (`app/celery_config.py`): Celery instance and configuration
2. **Tasks Module** (`app/tasks.py`): Async task definitions
3. **Worker Entry Point** (`celery_worker.py`): Command-line interface for workers
4. **Redis**: Message broker and result backend

## Prerequisites

### Local Development

1. **Redis Server**: Install and run Redis locally
   ```bash
   # macOS
   brew install redis
   brew services start redis
   
   # Ubuntu/Debian
   sudo apt-get install redis-server
   sudo systemctl start redis
   
   # Verify Redis is running
   redis-cli ping  # Should return "PONG"
   ```

2. **Environment Variables**: Set up your `.env` file
   ```bash
   cp .env.example .env
   # Edit .env and set REDIS_URL=redis://localhost:6379/0
   ```

## Running Celery

### Starting a Worker

A Celery worker processes tasks from the queue:

```bash
# Basic worker with info-level logging
python celery_worker.py worker --loglevel=info

# Worker with 4 concurrent processes
python celery_worker.py worker --loglevel=info --concurrency=4

# Worker with autoscaling (min 3, max 10 processes)
python celery_worker.py worker --loglevel=info --autoscale=10,3

# Worker with specific queues
python celery_worker.py worker --loglevel=info --queues=celery,priority

# Worker with debug logging
python celery_worker.py worker --loglevel=debug
```

### Starting the Beat Scheduler

The beat scheduler triggers periodic tasks:

```bash
# Start beat scheduler
python celery_worker.py beat --loglevel=info
```

### Running Both Worker and Beat

For development, you can run both in separate terminals:

```bash
# Terminal 1: Worker
python celery_worker.py worker --loglevel=info --concurrency=2

# Terminal 2: Beat
python celery_worker.py beat --loglevel=info
```

Or use a process manager like `honcho` or `foreman`:

```bash
# Install honcho
pip install honcho

# Run all processes from Procfile
honcho start
```

### Using Celery CLI Directly

You can also use the Celery command directly:

```bash
# Worker
celery -A app.celery_config worker --loglevel=info

# Beat
celery -A app.celery_config beat --loglevel=info

# Inspect active tasks
celery -A app.celery_config inspect active

# Inspect registered tasks
celery -A app.celery_config inspect registered
```

## Available Tasks

### Core Async Tasks

#### 1. Newsletter Generation
```python
from app.tasks import generate_newsletter_async

# Synchronous call (blocks until complete)
result = generate_newsletter_async("Artificial Intelligence", "concise")

# Asynchronous call (returns immediately)
task = generate_newsletter_async.delay("Artificial Intelligence", "concise")
result = task.get(timeout=300)  # Wait up to 5 minutes
```

#### 2. Email Sending
```python
from app.tasks import send_email_async

# Send email asynchronously
task = send_email_async.delay(
    "user@example.com",
    "Your Newsletter",
    "<h1>Content</h1>"
)
```

#### 3. Newsletter Issue (Combined)
```python
from app.tasks import send_newsletter_issue

# Generate and send newsletter
task = send_newsletter_issue.delay(
    newsletter_id=123,
    recipient_email="user@example.com"
)
```

### Periodic Tasks

These tasks are automatically scheduled via Celery Beat:

#### 1. Check Scheduled Newsletters
- **Schedule**: Every 15 minutes
- **Purpose**: Check for newsletters that need to be sent
- **Task**: `app.tasks.check_scheduled_newsletters`

#### 2. Cleanup Old Results
- **Schedule**: Daily at 2 AM UTC
- **Purpose**: Remove old task results from backend
- **Task**: `app.tasks.cleanup_old_results`

### Example Tasks

#### 1. Notification Task
```python
from app.tasks import example_notification_task

task = example_notification_task.delay(user_id=123, message="Hello!")
```

#### 2. API Call Task
```python
from app.tasks import example_api_call_task

task = example_api_call_task.delay(
    endpoint="https://api.example.com/data",
    method="POST",
    data={"key": "value"}
)
```

## Monitoring

### Worker Status

Check worker status and active tasks:

```bash
# List active tasks
celery -A app.celery_config inspect active

# List scheduled tasks
celery -A app.celery_config inspect scheduled

# List registered tasks
celery -A app.celery_config inspect registered

# Worker statistics
celery -A app.celery_config inspect stats

# Active queues
celery -A app.celery_config inspect active_queues
```

### Task Status via API

The application provides an API endpoint to check task status:

```bash
# Submit a task
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI News", "style": "concise"}'

# Response includes task_id
# {"status": "processing", "topic": "AI News", "task_id": "abc-123-def"}

# Check task status
curl http://localhost:5000/api/task/abc-123-def

# Response shows current state
# {"state": "SUCCESS", "result": {...}}
```

### Redis Monitoring

Monitor Redis directly:

```bash
# Connect to Redis CLI
redis-cli

# Monitor real-time commands
MONITOR

# Check queue length
LLEN celery

# Check result keys
KEYS celery-task-meta-*

# Get info about Redis
INFO
```

## Configuration

### Key Configuration Options

The Celery configuration is defined in `app/celery_config.py`:

```python
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Result expiration
    result_expires=3600,  # 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Error handling
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
```

### Environment Variables

- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379/0`)
- `CELERY_BROKER_URL`: Override broker URL (optional)
- `CELERY_RESULT_BACKEND`: Override result backend URL (optional)

## Error Handling and Retries

### Automatic Retries

Tasks are configured with automatic retries and exponential backoff:

```python
@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def my_task(self, arg):
    try:
        # Task logic
        pass
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### Task Callbacks

All tasks use the `CallbackTask` base class which provides:
- Success logging
- Failure logging
- Retry logging

### Error Recovery

If a worker crashes:
- Tasks are requeued due to `task_acks_late=True`
- Workers reject lost tasks via `task_reject_on_worker_lost=True`

## Production Deployment

### Heroku Deployment

1. **Add Redis Add-on**:
   ```bash
   heroku addons:create heroku-redis:mini
   ```

2. **Scale Worker Processes**:
   ```bash
   # Scale worker dynos
   heroku ps:scale worker=2
   
   # Scale beat scheduler (only 1 needed)
   heroku ps:scale beat=1
   ```

3. **Monitor Workers**:
   ```bash
   # Check worker status
   heroku ps
   
   # View worker logs
   heroku logs --dyno=worker --tail
   
   # View beat logs
   heroku logs --dyno=beat --tail
   ```

### Small-Scale Production

For small-scale production workloads:

1. **Single Worker**: Start with 1 worker with concurrency of 2-4
2. **Beat Scheduler**: Always run exactly 1 beat scheduler
3. **Redis**: Use a managed Redis service (Redis Labs, AWS ElastiCache, etc.)
4. **Monitoring**: Set up basic monitoring with Celery Flower (optional)

### Using Flower for Monitoring (Optional)

Flower is a web-based monitoring tool for Celery:

```bash
# Install flower
pip install flower

# Start Flower
celery -A app.celery_config flower --port=5555

# Access at http://localhost:5555
```

## Troubleshooting

### Common Issues

#### 1. Redis Connection Error

**Symptom**: `celery.exceptions.OperationalError: Error 111 connecting to localhost:6379`

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
# macOS: brew services start redis
# Linux: sudo systemctl start redis

# Check REDIS_URL environment variable
echo $REDIS_URL
```

#### 2. Tasks Not Executing

**Symptom**: Tasks are submitted but never complete

**Solution**:
```bash
# Check if worker is running
celery -A app.celery_config inspect active

# Check worker logs for errors
python celery_worker.py worker --loglevel=debug

# Verify tasks are registered
celery -A app.celery_config inspect registered
```

#### 3. Import Errors

**Symptom**: `ImportError: No module named 'app.tasks'`

**Solution**:
```bash
# Ensure you're in the correct directory
cd /path/to/thinkwrapper

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Reinstall dependencies
pip install -r requirements.txt
```

#### 4. Task Stuck in PENDING State

**Symptom**: Task status remains PENDING indefinitely

**Solution**:
- Check if worker is running and processing tasks
- Verify worker is connected to the correct broker
- Check for task routing configuration issues
- Review worker logs for errors

#### 5. Memory Issues

**Symptom**: Worker consumes too much memory

**Solution**:
```python
# Limit tasks per worker child process
worker_max_tasks_per_child=1000  # Restart worker after 1000 tasks

# Or start worker with lower concurrency
python celery_worker.py worker --concurrency=2
```

### Debugging Tips

1. **Enable Debug Logging**:
   ```bash
   python celery_worker.py worker --loglevel=debug
   ```

2. **Test Tasks in Python Shell**:
   ```python
   from app.tasks import generate_newsletter_async
   result = generate_newsletter_async.delay("Test Topic")
   print(result.state)  # Check state
   print(result.result)  # Get result (blocks until complete)
   ```

3. **Inspect Redis Directly**:
   ```bash
   redis-cli
   KEYS *  # See all keys
   LLEN celery  # Check queue length
   ```

4. **Purge All Tasks**:
   ```bash
   celery -A app.celery_config purge
   ```

5. **Check Worker Events**:
   ```bash
   celery -A app.celery_config events
   ```

## Testing

### Running Tests

Tests for Celery tasks are located in `tests/test_tasks.py`:

```bash
# Run all tests
pytest

# Run only Celery task tests
pytest tests/test_tasks.py

# Run with verbose output
pytest tests/test_tasks.py -v
```

### Writing Tests

Example test for a Celery task:

```python
from unittest.mock import patch
from app.tasks import generate_newsletter_async

@patch('app.services.generate_newsletter_content')
def test_generate_newsletter_task(mock_generate):
    mock_generate.return_value = {
        'subject': 'Test Subject',
        'content': 'Test Content'
    }
    
    result = generate_newsletter_async("Test Topic")
    
    assert result['subject'] == 'Test Subject'
    assert result['content'] == 'Test Content'
```

## Best Practices

1. **Keep Tasks Idempotent**: Tasks should produce the same result when run multiple times
2. **Use Task IDs**: Always store and track task IDs for status checking
3. **Set Timeouts**: Use `get(timeout=X)` when waiting for task results
4. **Monitor Queue Length**: Keep an eye on queue size to detect backlog
5. **Log Everything**: Use proper logging in tasks for debugging
6. **Handle Failures**: Implement proper error handling and retry logic
7. **Scale Appropriately**: Start with few workers and scale based on queue depth
8. **Use Separate Queues**: For priority tasks, use separate queues
9. **Clean Up Results**: Regularly clean up old results to prevent storage bloat
10. **Test Thoroughly**: Test tasks in isolation and with actual workers

## Performance Tuning

### Worker Optimization

```bash
# Adjust concurrency based on CPU cores
python celery_worker.py worker --concurrency=4

# Use autoscaling
python celery_worker.py worker --autoscale=10,3

# Adjust prefetch multiplier (lower = better for long tasks)
# Set in celery_config.py: worker_prefetch_multiplier=1
```

### Redis Optimization

```python
# Increase result expiration for short-lived results
result_expires=1800  # 30 minutes instead of 1 hour

# Use compression for large results
result_compression='gzip'
```

## Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html#best-practices)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Monitoring Tool](https://flower.readthedocs.io/)

## Support

For issues specific to ThinkWrapper's Celery setup:
1. Check this documentation
2. Review worker logs
3. Inspect Redis for queue status
4. Test tasks in isolation
5. Open an issue on GitHub with logs and configuration details
