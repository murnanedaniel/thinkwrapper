"""Tests for Celery tasks."""
import pytest
from unittest.mock import patch, Mock, MagicMock, PropertyMock
from datetime import datetime, timedelta, timezone
from celery.exceptions import MaxRetriesExceededError


class TestNewsletterGenerationTask:
    """Test async newsletter generation task."""

    @patch('app.claude_service.generate_newsletter_with_search')
    def test_generate_newsletter_async_success(self, mock_search):
        """Test successful newsletter generation."""
        from app.tasks import generate_newsletter_async

        mock_search.return_value = {
            'subject': 'AI Weekly Update',
            'content': 'Great content about AI...'
        }

        result = generate_newsletter_async("Artificial Intelligence", "professional")

        assert result is not None
        assert result['subject'] == 'AI Weekly Update'
        assert result['content'] == 'Great content about AI...'

    @patch('app.claude_service.generate_newsletter_with_search')
    def test_generate_newsletter_async_with_default_style(self, mock_search):
        """Test newsletter generation with default style."""
        from app.tasks import generate_newsletter_async

        mock_search.return_value = {
            'subject': 'Test Subject',
            'content': 'Test Content'
        }

        result = generate_newsletter_async("Test Topic")
        assert result is not None
        assert result['subject'] == 'Test Subject'

    @patch('app.claude_service.generate_newsletter_content_claude')
    @patch('app.claude_service.generate_newsletter_with_search')
    def test_generate_newsletter_async_fallback_to_claude(self, mock_search, mock_claude):
        """Test fallback to direct Claude when search fails."""
        from app.tasks import generate_newsletter_async

        mock_search.return_value = None
        mock_claude.return_value = {
            'subject': 'Fallback Subject',
            'content': 'Fallback Content'
        }

        result = generate_newsletter_async("Test Topic")
        assert result is not None
        assert result['subject'] == 'Fallback Subject'

    @patch('app.claude_service.generate_newsletter_content_claude')
    @patch('app.claude_service.generate_newsletter_with_search')
    def test_generate_newsletter_async_total_failure(self, mock_search, mock_claude):
        """Test when both generation methods fail."""
        from app.tasks import generate_newsletter_async

        mock_search.return_value = None
        mock_claude.return_value = None

        # In eager mode, Celery raises the exception rather than retrying
        with pytest.raises(Exception):
            generate_newsletter_async("Test Topic")


class TestEmailSendingTask:
    """Test async email sending task."""

    @patch('app.services.send_email')
    def test_send_email_async_success(self, mock_send):
        """Test successful email sending."""
        from app.tasks import send_email_async

        mock_send.return_value = True

        result = send_email_async("test@example.com", "Subject", "<p>Content</p>")

        assert result['success'] is True
        assert result['to_email'] == 'test@example.com'
        mock_send.assert_called_once_with("test@example.com", "Subject", "<p>Content</p>")

    @patch('app.services.send_email')
    def test_send_email_async_failure(self, mock_send):
        """Test email sending failure."""
        from app.tasks import send_email_async

        mock_send.return_value = False

        # In eager mode, Celery raises the exception rather than retrying
        with pytest.raises(Exception):
            send_email_async("test@example.com", "Subject", "Content")


class TestNewsletterIssueTask:
    """Test newsletter issue sending task."""

    @patch('app.services.send_email')
    @patch('app.claude_service.generate_newsletter_with_search')
    @patch('app.tasks._get_db_session')
    def test_send_newsletter_issue_success(self, mock_db_session, mock_search, mock_send):
        """Test successful newsletter issue creation and sending."""
        from app.tasks import send_newsletter_issue
        from app.models import Newsletter

        mock_db = MagicMock()
        mock_db_session.return_value = mock_db

        mock_newsletter = Mock(spec=Newsletter)
        mock_newsletter.id = 1
        mock_newsletter.topic = 'AI News'
        mock_newsletter.description = 'Latest AI developments'
        mock_newsletter.style = 'professional'
        mock_db.query.return_value.get.return_value = mock_newsletter

        mock_search.return_value = {
            'subject': 'This Week in AI',
            'content': '## AI News\n\nContent here...'
        }
        mock_send.return_value = True

        result = send_newsletter_issue(1, 'user@example.com')

        assert result['success'] is True
        assert result['newsletter_id'] == 1
        assert result['email_sent'] is True

    @patch('app.tasks._get_db_session')
    def test_send_newsletter_issue_not_found(self, mock_db_session):
        """Test sending issue for non-existent newsletter."""
        from app.tasks import send_newsletter_issue

        mock_db = MagicMock()
        mock_db_session.return_value = mock_db
        mock_db.query.return_value.get.return_value = None

        # In eager mode, Celery raises the exception rather than retrying
        with pytest.raises(Exception):
            send_newsletter_issue(999, 'user@example.com')


class TestPeriodicTasks:
    """Test periodic/scheduled tasks."""

    @patch('app.tasks.send_newsletter_issue')
    @patch('app.tasks._get_db_session')
    def test_check_scheduled_newsletters(self, mock_db_session, mock_send_issue):
        """Test scheduled newsletter check."""
        from app.tasks import check_scheduled_newsletters

        mock_db = MagicMock()
        mock_db_session.return_value = mock_db

        # Create mock newsletter that's due
        mock_newsletter = Mock()
        mock_newsletter.id = 1
        mock_newsletter.schedule = 'daily'
        mock_newsletter.status = 'active'
        mock_newsletter.last_sent_at = datetime.utcnow() - timedelta(days=2)
        mock_user = Mock()
        mock_user.email = 'user@example.com'
        mock_user.subscription_status = 'active'
        mock_newsletter.user = mock_user

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_newsletter]

        result = check_scheduled_newsletters()

        assert result['success'] is True
        assert result['checked'] == 1
        mock_send_issue.delay.assert_called_once_with(1, 'user@example.com')

    def test_cleanup_old_results(self):
        """Test cleanup task runs successfully."""
        from app.tasks import cleanup_old_results

        result = cleanup_old_results()
        assert result['success'] is True
        assert 'cleaned_at' in result


class TestCallbackTask:
    """Test the CallbackTask base class."""

    def test_callback_task_on_success(self):
        """Test CallbackTask logs success."""
        from app.tasks import CallbackTask

        task = CallbackTask()
        task.name = 'test_task'
        # Should not raise
        task.on_success('result', 'task-id-123', [], {})

    def test_callback_task_on_failure(self):
        """Test CallbackTask logs failure."""
        from app.tasks import CallbackTask

        task = CallbackTask()
        task.name = 'test_task'
        # Should not raise
        task.on_failure(Exception('test error'), 'task-id-123', [], {}, None)
