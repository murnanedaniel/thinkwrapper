"""
User Journey Tests

This module tests complete user journeys through the application,
validating end-to-end functionality from the user's perspective.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from app import create_app


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
    })
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Create an application context."""
    with app.app_context():
        yield


class TestSignupJourney:
    """Test the complete user signup journey via OAuth."""

    @pytest.mark.skip(reason="Network access to Google OAuth not available in sandbox environment")
    def test_auth_endpoint_exists(self, client):
        """Verify auth login endpoint exists and returns redirect."""
        response = client.get('/api/auth/login')
        # Should redirect to Google OAuth (302) or return error if not configured
        assert response.status_code in [302, 500]

    def test_user_endpoint_unauthenticated(self, client):
        """Verify unauthenticated user response."""
        response = client.get('/api/auth/user')
        assert response.status_code == 200
        assert response.json['authenticated'] is False

    @patch('app.auth_routes.oauth')
    @patch('app.auth_routes.login_user')
    @patch('app.auth_routes.get_db_session')
    def test_oauth_callback_creates_user(self, mock_db, mock_login, mock_oauth, client):
        """Test OAuth callback creates new user."""
        # Mock OAuth token response
        mock_oauth.google.authorize_access_token.return_value = {
            'userinfo': {
                'sub': 'google-user-123',
                'email': 'test@example.com',
                'name': 'Test User'
            }
        }

        # Mock database session
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_db.return_value = mock_session

        response = client.get('/api/auth/callback')

        # Should redirect to home after successful auth
        assert response.status_code == 302
        assert mock_session.add.called
        assert mock_session.commit.called

    def test_logout_endpoint_exists(self, client):
        """Verify logout endpoint exists."""
        response = client.get('/api/auth/logout')
        # Should redirect (302) even if not logged in
        assert response.status_code in [302, 401]


class TestNewsletterCreationJourney:
    """Test the complete newsletter creation journey."""

    def test_generate_endpoint_requires_json(self, client):
        """Verify generate endpoint requires JSON content type."""
        response = client.post('/api/generate', data='not json')
        assert response.status_code == 415
        assert response.json['success'] is False

    def test_generate_endpoint_validates_topic(self, client):
        """Verify topic validation."""
        # Empty topic
        response = client.post('/api/generate', json={'topic': ''})
        assert response.status_code == 400
        assert response.json['success'] is False
        assert 'Topic' in response.json['error']

        # Topic too short
        response = client.post('/api/generate', json={'topic': 'ab'})
        assert response.status_code == 400
        assert response.json['success'] is False

    def test_generate_endpoint_validates_style(self, client):
        """Verify style validation."""
        response = client.post('/api/generate', json={
            'topic': 'Valid topic here',
            'style': 'invalid_style'
        })
        assert response.status_code == 400
        assert response.json['success'] is False
        assert 'style' in response.json['error'].lower()

    @patch('app.tasks.generate_newsletter_async')
    def test_generate_newsletter_success(self, mock_task, client):
        """Test successful newsletter generation queuing."""
        mock_result = Mock()
        mock_result.id = 'test-task-123'
        mock_task.delay.return_value = mock_result

        response = client.post('/api/generate', json={
            'topic': 'Artificial Intelligence',
            'style': 'professional'
        })

        assert response.status_code == 202
        assert response.json['success'] is True
        assert response.json['status'] == 'processing'
        assert response.json['task_id'] == 'test-task-123'
        mock_task.delay.assert_called_once()

    @patch('app.celery_config.celery.AsyncResult')
    def test_task_status_polling(self, mock_async_result, client):
        """Test task status polling flow."""
        # Test PENDING state
        mock_task = Mock()
        mock_task.state = 'PENDING'
        mock_async_result.return_value = mock_task

        response = client.get('/api/task/test-task-id')
        assert response.status_code == 200
        assert response.json['state'] == 'PENDING'

        # Test SUCCESS state
        mock_task.state = 'SUCCESS'
        mock_task.result = {
            'subject': 'AI Newsletter',
            'content': 'Newsletter content here'
        }
        mock_async_result.return_value = mock_task

        response = client.get('/api/task/test-task-id')
        assert response.status_code == 200
        assert response.json['state'] == 'SUCCESS'
        assert 'result' in response.json

    @patch('app.tasks.generate_newsletter_async')
    def test_full_newsletter_creation_flow(self, mock_task, client):
        """Test the complete newsletter creation flow."""
        # Step 1: Queue newsletter generation
        mock_result = Mock()
        mock_result.id = 'flow-test-task'
        mock_task.delay.return_value = mock_result

        response = client.post('/api/generate', json={
            'topic': 'Weekly Tech News',
            'style': 'casual'
        })

        assert response.status_code == 202
        task_id = response.json['task_id']
        assert task_id == 'flow-test-task'



class TestPaymentJourney:
    """Test the payment and subscription journey."""

    def test_checkout_requires_json(self, client):
        """Verify checkout endpoint requires JSON."""
        response = client.post('/api/payment/checkout', data='not json')
        assert response.status_code == 415

    def test_checkout_validates_required_fields(self, client):
        """Verify required field validation."""
        # Missing price_id
        response = client.post('/api/payment/checkout', json={
            'customer_email': 'test@example.com',
            'success_url': 'https://example.com/success'
        })
        assert response.status_code == 400
        assert 'price_id' in response.json['error']

        # Invalid email
        response = client.post('/api/payment/checkout', json={
            'price_id': 'pri_123',
            'customer_email': 'invalid-email',
            'success_url': 'https://example.com/success'
        })
        assert response.status_code == 400
        assert 'email' in response.json['error'].lower()

    @patch('app.payment_service.get_paddle_service')
    def test_checkout_success(self, mock_get_service, client):
        """Test successful checkout session creation."""
        mock_service = Mock()
        mock_service.create_checkout_session.return_value = {
            'data': {
                'url': 'https://checkout.paddle.com/test',
                'id': 'ses_123'
            }
        }
        mock_get_service.return_value = mock_service

        response = client.post('/api/payment/checkout', json={
            'price_id': 'pri_monthly',
            'customer_email': 'user@example.com',
            'success_url': 'https://example.com/success'
        })

        assert response.status_code == 200
        assert response.json['success'] is True
        assert 'checkout_url' in response.json['data']

    def test_webhook_requires_signature(self, client):
        """Verify webhook requires Paddle-Signature header."""
        response = client.post('/api/payment/webhook', json={
            'event_type': 'transaction.completed',
            'data': {}
        })
        assert response.status_code == 400
        assert 'signature' in response.json['error'].lower()

    @patch('app.payment_service.get_paddle_service')
    def test_webhook_verifies_signature(self, mock_get_service, client):
        """Verify webhook signature verification."""
        mock_service = Mock()
        mock_service.verify_webhook_signature.return_value = False
        mock_get_service.return_value = mock_service

        response = client.post(
            '/api/payment/webhook',
            json={'event_type': 'transaction.completed', 'data': {}},
            headers={'Paddle-Signature': 'invalid-sig'}
        )

        assert response.status_code == 401
        assert 'signature' in response.json['error'].lower()

    @patch('app.payment_service.get_paddle_service')
    def test_webhook_processes_transaction(self, mock_get_service, client):
        """Test successful webhook processing."""
        mock_service = Mock()
        mock_service.verify_webhook_signature.return_value = True
        mock_service.process_webhook_event.return_value = {
            'status': 'success',
            'event_type': 'transaction.completed'
        }
        mock_get_service.return_value = mock_service

        response = client.post(
            '/api/payment/webhook',
            json={
                'event_type': 'transaction.completed',
                'data': {'id': 'txn_123', 'customer_id': 'cus_456'}
            },
            headers={'Paddle-Signature': 'valid-sig'}
        )

        assert response.status_code == 200
        assert response.json['success'] is True


class TestClaudeAPIJourney:
    """Test the Claude API integration journey."""

    def test_claude_newsletter_validates_topic(self, client):
        """Verify newsletter topic validation."""
        response = client.post('/api/claude/newsletter', json={
            'topic': ''
        })
        assert response.status_code == 400

    @patch('app.claude_service.generate_newsletter_with_search')
    def test_claude_newsletter_success(self, mock_search, client):
        """Test successful Claude newsletter generation."""
        mock_search.return_value = {
            'subject': 'AI Newsletter',
            'content': 'Newsletter content here',
            'model': 'claude-haiku-4-5',
            'usage': {'input_tokens': 50, 'output_tokens': 500},
            'articles': [{'title': 'Test Article', 'url': 'https://example.com', 'description': 'Test'}],
            'search_source': 'mock',
            'total_articles': 1
        }

        response = client.post('/api/claude/newsletter', json={
            'topic': 'Machine Learning Trends',
            'style': 'technical'
        })

        assert response.status_code == 200
        assert response.json['success'] is True
        assert 'subject' in response.json['data']
        assert 'content' in response.json['data']


class TestInputValidation:
    """Test input validation across all journeys."""

    def test_xss_prevention_in_topic(self, client):
        """Verify XSS prevention in topic field."""
        response = client.post('/api/generate', json={
            'topic': '<script>alert("xss")</script>Valid topic'
        })
        # Should reject due to injection pattern
        assert response.status_code == 400
        assert 'invalid' in response.json['error'].lower()

    def test_topic_length_limits(self, client):
        """Verify topic length limits."""
        # Too short
        response = client.post('/api/generate', json={'topic': 'ab'})
        assert response.status_code == 400

        # Too long (over 500 chars)
        long_topic = 'a' * 501
        response = client.post('/api/generate', json={'topic': long_topic})
        assert response.status_code == 400

    def test_email_validation(self, client):
        """Verify email validation across endpoints."""
        invalid_emails = [
            'not-an-email',
            'missing@domain',
            '@nodomain.com',
            'spaces in@email.com',
        ]

        for email in invalid_emails:
            response = client.post('/api/payment/checkout', json={
                'price_id': 'pri_123',
                'customer_email': email,
                'success_url': 'https://example.com'
            })
            assert response.status_code == 400, f"Email {email} should be invalid"


