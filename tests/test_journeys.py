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

    @patch('app.routes.generate_newsletter_async')
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

    @patch('app.routes.generate_newsletter_async')
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


class TestAdminSynthesisJourney:
    """Test the admin newsletter synthesis journey."""

    def test_synthesize_requires_json(self, client):
        """Verify synthesize endpoint requires JSON."""
        response = client.post('/api/admin/synthesize', data='not json')
        assert response.status_code == 415

    def test_synthesize_validates_required_fields(self, client):
        """Verify required field validation."""
        # Missing newsletter_id
        response = client.post('/api/admin/synthesize', json={
            'topic': 'Test Topic'
        })
        assert response.status_code == 400
        assert 'newsletter_id' in response.json['error']

        # Missing topic
        response = client.post('/api/admin/synthesize', json={
            'newsletter_id': 1
        })
        assert response.status_code == 400
        assert 'Topic' in response.json['error']

    def test_synthesize_validates_email_when_sending(self, client):
        """Verify email validation when send_email is true."""
        response = client.post('/api/admin/synthesize', json={
            'newsletter_id': 1,
            'topic': 'Test Newsletter',
            'send_email': True,
            'email_to': 'invalid-email'
        })
        assert response.status_code == 400
        assert 'email' in response.json['error'].lower()

    @patch('app.routes.NewsletterSynthesizer')
    @patch('app.routes.NewsletterRenderer')
    def test_synthesize_success(self, mock_renderer_cls, mock_synth_cls, client):
        """Test successful newsletter synthesis."""
        # Mock synthesizer
        mock_synth = Mock()
        mock_synth.generate_on_demand.return_value = {
            'success': True,
            'subject': 'Test Subject',
            'content': 'Test Content',
            'content_items_count': 2,
            'generated_at': '2026-01-02T12:00:00Z',
            'style': 'professional'
        }
        mock_synth_cls.return_value = mock_synth

        # Mock renderer
        mock_renderer = Mock()
        mock_renderer.render_html.return_value = '<html>Test</html>'
        mock_renderer_cls.return_value = mock_renderer

        response = client.post('/api/admin/synthesize', json={
            'newsletter_id': 1,
            'topic': 'AI Weekly Update',
            'style': 'professional',
            'format': 'html'
        })

        assert response.status_code == 200
        assert response.json['success'] is True
        assert 'data' in response.json


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


class TestPreviewJourney:
    """Test the newsletter preview journey."""

    def test_preview_requires_json(self, client):
        """Verify preview endpoint requires JSON."""
        response = client.post('/api/admin/newsletter/preview', data='not json')
        assert response.status_code == 415

    def test_preview_validates_required_fields(self, client):
        """Verify required field validation."""
        # Missing subject
        response = client.post('/api/admin/newsletter/preview', json={
            'content': 'Some content'
        })
        assert response.status_code == 400
        assert 'subject' in response.json['error']

        # Missing content
        response = client.post('/api/admin/newsletter/preview', json={
            'subject': 'Test Subject'
        })
        assert response.status_code == 400
        assert 'content' in response.json['error']

    def test_preview_validates_format(self, client):
        """Verify format validation."""
        response = client.post('/api/admin/newsletter/preview', json={
            'subject': 'Test Subject',
            'content': 'Test content',
            'format': 'invalid'
        })
        assert response.status_code == 400
        assert 'format' in response.json['error'].lower()

    def test_preview_success_html(self, client):
        """Test successful HTML preview."""
        response = client.post('/api/admin/newsletter/preview', json={
            'subject': 'Weekly Digest',
            'content': '# Welcome\n\nThis is the newsletter.',
            'format': 'html'
        })

        assert response.status_code == 200
        assert response.json['success'] is True
        assert 'rendered' in response.json['data']
        assert 'html' in response.json['data']['rendered']

    def test_preview_success_both_formats(self, client):
        """Test preview with both formats."""
        response = client.post('/api/admin/newsletter/preview', json={
            'subject': 'Weekly Digest',
            'content': 'Newsletter content here',
            'format': 'both'
        })

        assert response.status_code == 200
        rendered = response.json['data']['rendered']
        assert 'html' in rendered
        assert 'text' in rendered


class TestClaudeAPIJourney:
    """Test the Claude API integration journey."""

    def test_claude_generate_requires_json(self, client):
        """Verify Claude generate requires JSON."""
        response = client.post('/api/claude/generate', data='not json')
        assert response.status_code == 415

    def test_claude_generate_validates_prompt(self, client):
        """Verify prompt validation."""
        response = client.post('/api/claude/generate', json={'prompt': ''})
        assert response.status_code == 400
        assert 'prompt' in response.json['error'].lower() or 'provided' in response.json['error'].lower()

    @patch('app.routes.claude_service')
    def test_claude_generate_success(self, mock_claude, client):
        """Test successful Claude text generation."""
        mock_claude.generate_text.return_value = {
            'text': 'Generated response',
            'model': 'claude-haiku-4-5',
            'usage': {'input_tokens': 10, 'output_tokens': 50},
            'stop_reason': 'end_turn'
        }

        response = client.post('/api/claude/generate', json={
            'prompt': 'Explain AI in simple terms'
        })

        assert response.status_code == 200
        assert response.json['success'] is True
        assert 'text' in response.json['data']

    def test_claude_newsletter_validates_topic(self, client):
        """Verify newsletter topic validation."""
        response = client.post('/api/claude/newsletter', json={
            'topic': ''
        })
        assert response.status_code == 400

    @patch('app.routes.claude_service')
    def test_claude_newsletter_success(self, mock_claude, client):
        """Test successful Claude newsletter generation."""
        mock_claude.generate_newsletter_content_claude.return_value = {
            'subject': 'AI Newsletter',
            'content': 'Newsletter content here',
            'model': 'claude-haiku-4-5',
            'usage': {'input_tokens': 50, 'output_tokens': 500}
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


class TestConfigurationJourney:
    """Test newsletter configuration journey."""

    def test_get_config(self, client):
        """Test getting newsletter configuration."""
        response = client.get('/api/admin/newsletter/config')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert 'data' in response.json

        config = response.json['data']
        assert 'schedule' in config
        assert 'delivery_format' in config
        assert 'style' in config

    def test_update_config_invalid(self, client):
        """Test updating config with invalid values."""
        response = client.post('/api/admin/newsletter/config', json={
            'schedule': 'invalid_schedule'
        })
        assert response.status_code == 400

    def test_update_config_valid(self, client):
        """Test updating config with valid values."""
        response = client.post('/api/admin/newsletter/config', json={
            'schedule': 'weekly',
            'style': 'professional',
            'delivery_format': 'html'
        })
        assert response.status_code == 200
        assert response.json['success'] is True
