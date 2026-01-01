"""Tests for Celery tasks."""
import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime
from celery.exceptions import MaxRetriesExceededError


class TestNewsletterGenerationTask:
    """Test async newsletter generation task."""
    
    @patch('app.tasks.services.generate_newsletter_content')
    def test_generate_newsletter_async_success(self, mock_generate):
        """Test successful newsletter generation."""
        from app.tasks import generate_newsletter_async
        
        mock_generate.return_value = {
            'subject': 'AI Weekly Update',
            'content': 'Great content about AI...'
        }
        
        result = generate_newsletter_async("Artificial Intelligence", "concise")
        
        assert result is not None
        assert result['subject'] == 'AI Weekly Update'
        assert result['content'] == 'Great content about AI...'
        mock_generate.assert_called_once_with("Artificial Intelligence", "concise")
    
    @patch('app.tasks.services.generate_newsletter_content')
    def test_generate_newsletter_async_with_default_style(self, mock_generate):
        """Test newsletter generation with default style."""
        from app.tasks import generate_newsletter_async
        
        mock_generate.return_value = {
            'subject': 'Test Subject',
            'content': 'Test Content'
        }
        
        result = generate_newsletter_async("Test Topic")
        
        assert result is not None
        mock_generate.assert_called_once_with("Test Topic", "concise")
    
    @patch('app.tasks.services.generate_newsletter_content')
    def test_generate_newsletter_async_none_result(self, mock_generate):
        """Test handling when service returns None."""
        from app.tasks import generate_newsletter_async
        
        mock_generate.return_value = None
        
        # Create a mock task instance
        mock_task = MagicMock()
        mock_task.request.retries = 0
        mock_task.retry.side_effect = Exception("Retry")
        
        with patch.object(generate_newsletter_async, 'request'):
            with patch.object(generate_newsletter_async, 'retry', side_effect=Exception("Retry")):
                with pytest.raises(Exception):
                    generate_newsletter_async("Test Topic")


class TestEmailSendingTask:
    """Test async email sending task."""
    
    @patch('app.tasks.services.send_email')
    def test_send_email_async_success(self, mock_send):
        """Test successful email sending."""
        from app.tasks import send_email_async
        
        mock_send.return_value = True
        
        result = send_email_async(
            "test@example.com",
            "Test Subject",
            "<h1>Test Content</h1>"
        )
        
        assert result['success'] is True
        assert result['to_email'] == "test@example.com"
        assert result['subject'] == "Test Subject"
        assert 'sent_at' in result
        mock_send.assert_called_once_with(
            "test@example.com",
            "Test Subject",
            "<h1>Test Content</h1>"
        )
    
    @patch('app.tasks.services.send_email')
    def test_send_email_async_failure(self, mock_send):
        """Test handling of email sending failure."""
        from app.tasks import send_email_async
        
        mock_send.return_value = False
        
        # Mock the retry mechanism
        mock_task = MagicMock()
        mock_task.request.retries = 0
        mock_task.retry.side_effect = Exception("Retry")
        
        with patch.object(send_email_async, 'request'):
            with patch.object(send_email_async, 'retry', side_effect=Exception("Retry")):
                with pytest.raises(Exception):
                    send_email_async("test@example.com", "Subject", "Content")


class TestNewsletterIssueTask:
    """Test combined newsletter generation and sending task."""
    
    @patch('app.tasks.send_email_async')
    @patch('app.tasks.generate_newsletter_async')
    def test_send_newsletter_issue_success(self, mock_generate, mock_send):
        """Test successful newsletter issue processing."""
        from app.tasks import send_newsletter_issue
        
        # Mock AsyncResult for generate task
        mock_generate_result = Mock()
        mock_generate_result.get.return_value = {
            'subject': 'Newsletter Subject',
            'content': 'Newsletter Content'
        }
        mock_generate.apply_async.return_value = mock_generate_result
        
        # Mock AsyncResult for send task
        mock_send_result = Mock()
        mock_send_result.get.return_value = {'success': True}
        mock_send.apply_async.return_value = mock_send_result
        
        result = send_newsletter_issue(123, "user@example.com")
        
        assert result['success'] is True
        assert result['newsletter_id'] == 123
        assert result['recipient'] == "user@example.com"
        assert result['content_generated'] is True
        assert result['email_sent'] is True


class TestPeriodicTasks:
    """Test periodic tasks."""
    
    def test_check_scheduled_newsletters(self):
        """Test checking scheduled newsletters."""
        from app.tasks import check_scheduled_newsletters
        
        result = check_scheduled_newsletters()
        
        assert result['success'] is True
        assert 'checked' in result
        assert 'sent' in result
        assert 'checked_at' in result
    
    def test_cleanup_old_results(self):
        """Test cleanup of old task results."""
        from app.tasks import cleanup_old_results
        
        result = cleanup_old_results()
        
        assert result['success'] is True
        assert 'cleaned_at' in result
        assert 'message' in result


class TestExampleTasks:
    """Test example tasks."""
    
    def test_example_notification_task(self):
        """Test notification task."""
        from app.tasks import example_notification_task
        
        result = example_notification_task(user_id=123, message="Test notification")
        
        assert result['success'] is True
        assert result['user_id'] == 123
        assert result['message'] == "Test notification"
        assert 'sent_at' in result
    
    def test_example_api_call_task(self):
        """Test API call task."""
        from app.tasks import example_api_call_task
        
        result = example_api_call_task(
            endpoint="https://api.example.com/test",
            method="POST",
            data={"key": "value"}
        )
        
        assert result['success'] is True
        assert result['endpoint'] == "https://api.example.com/test"
        assert result['method'] == "POST"
        assert 'completed_at' in result


class TestCallbackTask:
    """Test callback task base class."""
    
    @patch('app.tasks.logger')
    def test_callback_task_on_success(self, mock_logger):
        """Test success callback logging."""
        from app.tasks import CallbackTask
        
        task = CallbackTask()
        task.name = "test_task"
        
        task.on_success("result", "task-id-123", [], {})
        
        # Verify logging was called
        assert mock_logger.info.called
    
    @patch('app.tasks.logger')
    def test_callback_task_on_failure(self, mock_logger):
        """Test failure callback logging."""
        from app.tasks import CallbackTask
        
        task = CallbackTask()
        task.name = "test_task"
        
        exc = Exception("Test error")
        task.on_failure(exc, "task-id-123", [], {}, None)
        
        # Verify error logging was called
        assert mock_logger.error.called
    
    @patch('app.tasks.logger')
    def test_callback_task_on_retry(self, mock_logger):
        """Test retry callback logging."""
        from app.tasks import CallbackTask
        
        task = CallbackTask()
        task.name = "test_task"
        
        exc = Exception("Test error")
        task.on_retry(exc, "task-id-123", [], {}, None)
        
        # Verify warning logging was called
        assert mock_logger.warning.called


class TestTaskConfiguration:
    """Test task configuration and setup."""
    
    def test_celery_instance_exists(self):
        """Test that Celery instance is properly configured."""
        from app.celery_config import celery
        
        assert celery is not None
        assert celery.conf.task_serializer == 'json'
        assert celery.conf.result_serializer == 'json'
        assert celery.conf.timezone == 'UTC'
    
    def test_tasks_registered(self):
        """Test that tasks are registered with Celery."""
        from app.celery_config import celery
        
        registered_tasks = list(celery.tasks.keys())
        
        # Check that our custom tasks are registered
        assert any('generate_newsletter_async' in task for task in registered_tasks)
        assert any('send_email_async' in task for task in registered_tasks)
    
    def test_beat_schedule_configured(self):
        """Test that beat schedule is configured."""
        from app.celery_config import celery
        
        beat_schedule = celery.conf.beat_schedule
        
        assert 'check-scheduled-newsletters' in beat_schedule
        assert 'cleanup-old-task-results' in beat_schedule
        
        # Verify schedule configuration
        newsletter_schedule = beat_schedule['check-scheduled-newsletters']
        assert newsletter_schedule['task'] == 'app.tasks.check_scheduled_newsletters'
        
        cleanup_schedule = beat_schedule['cleanup-old-task-results']
        assert cleanup_schedule['task'] == 'app.tasks.cleanup_old_results'


class TestTaskRetryLogic:
    """Test task retry behavior."""
    
    @patch('app.tasks.services.generate_newsletter_content')
    def test_generate_newsletter_retry_on_exception(self, mock_generate):
        """Test that task retries on exception."""
        from app.tasks import generate_newsletter_async
        
        mock_generate.side_effect = [
            Exception("First failure"),
            {'subject': 'Success', 'content': 'Content'}
        ]
        
        # Create a mock for the retry mechanism
        with patch.object(generate_newsletter_async, 'retry') as mock_retry:
            mock_retry.side_effect = Exception("Retry called")
            
            with pytest.raises(Exception):
                generate_newsletter_async("Test")
    
    @patch('app.tasks.services.send_email')
    def test_send_email_retry_on_failure(self, mock_send):
        """Test that email task retries on failure."""
        from app.tasks import send_email_async
        
        mock_send.side_effect = [False, True]
        
        # Mock the retry mechanism
        with patch.object(send_email_async, 'retry') as mock_retry:
            mock_retry.side_effect = Exception("Retry called")
            
            with pytest.raises(Exception):
                send_email_async("test@example.com", "Subject", "Content")


class TestTaskErrorHandling:
    """Test error handling in tasks."""
    
    @patch('app.tasks.services.generate_newsletter_content')
    @patch('app.tasks.logger')
    def test_generate_newsletter_logs_error(self, mock_logger, mock_generate):
        """Test that errors are properly logged."""
        from app.tasks import generate_newsletter_async
        
        mock_generate.side_effect = Exception("API Error")
        
        with patch.object(generate_newsletter_async, 'retry', side_effect=Exception("Retry")):
            with pytest.raises(Exception):
                generate_newsletter_async("Test Topic")
        
        # Verify error was logged
        assert mock_logger.error.called
    
    @patch('app.tasks.services.send_email')
    @patch('app.tasks.logger')
    def test_send_email_logs_error(self, mock_logger, mock_send):
        """Test that email errors are logged."""
        from app.tasks import send_email_async
        
        mock_send.side_effect = Exception("SendGrid Error")
        
        with patch.object(send_email_async, 'retry', side_effect=Exception("Retry")):
            with pytest.raises(Exception):
                send_email_async("test@example.com", "Subject", "Content")
        
        # Verify error was logged
        assert mock_logger.error.called
