"""
Integration tests for Mailjet email functionality.

These tests verify email sending with both mocked and real Mailjet API.
The real API tests require MAILJET_API_KEY and MAILJET_API_SECRET environment variables.
"""

import os
import pytest
from unittest.mock import patch, Mock
from app import services
from app.email_templates import get_newsletter_template, get_welcome_template, get_test_template


class TestEmailTemplates:
    """Test email template generation."""
    
    def test_newsletter_template_basic(self):
        """Test basic newsletter template generation."""
        subject = "Weekly Update"
        content = "<p>This is the newsletter content.</p>"
        
        html = get_newsletter_template(subject, content)
        
        assert subject in html
        assert content in html
        assert "ThinkWrapper Newsletter" in html
        assert "<!DOCTYPE html>" in html
        assert "Unsubscribe" in html
    
    def test_newsletter_template_with_kwargs(self):
        """Test newsletter template with custom parameters."""
        subject = "Custom Newsletter"
        content = "<p>Custom content</p>"
        preheader = "Custom preheader text"
        unsubscribe_link = "https://example.com/unsubscribe"
        
        html = get_newsletter_template(
            subject, 
            content, 
            preheader=preheader,
            unsubscribe_link=unsubscribe_link
        )
        
        assert preheader in html
        assert unsubscribe_link in html
    
    def test_welcome_template(self):
        """Test welcome email template."""
        user_name = "John Doe"
        
        html = get_welcome_template(user_name)
        
        assert user_name in html
        assert "Welcome to ThinkWrapper" in html
        assert "<!DOCTYPE html>" in html
    
    def test_welcome_template_default_name(self):
        """Test welcome template with default subscriber name."""
        html = get_welcome_template()
        
        assert "Valued Subscriber" in html
        assert "Welcome to ThinkWrapper" in html
    
    def test_test_template(self):
        """Test the test email template."""
        html = get_test_template()
        
        assert "Test Email" in html
        assert "Mailjet integration" in html
        assert "<!DOCTYPE html>" in html


class TestEmailIntegration:
    """Integration tests for email sending with Mailjet."""
    
    @patch("app.services.Client")
    @patch.dict(os.environ, {"MAILJET_API_KEY": "test-api-key", "MAILJET_API_SECRET": "test-api-secret"})
    def test_send_email_with_template(self, mock_mailjet_client, app_context):
        """Test sending email with HTML template."""
        # Mock Mailjet client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_send = Mock()
        mock_send.create = Mock(return_value=mock_response)
        mock_client.send = mock_send
        mock_mailjet_client.return_value = mock_client
        
        # Use email template
        html_content = get_test_template()
        
        result = services.send_email(
            "test@example.com",
            "Test Email - Mailjet Integration",
            html_content
        )
        
        assert result is True
        mock_mailjet_client.assert_called_once()
        mock_send.create.assert_called_once()
    
    @patch("app.services.Client")
    @patch.dict(os.environ, {"MAILJET_API_KEY": "test-api-key", "MAILJET_API_SECRET": "test-api-secret"})
    def test_send_welcome_email(self, mock_mailjet_client, app_context):
        """Test sending welcome email with template."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_send = Mock()
        mock_send.create = Mock(return_value=mock_response)
        mock_client.send = mock_send
        mock_mailjet_client.return_value = mock_client
        
        html_content = get_welcome_template("Jane Doe")
        
        result = services.send_email(
            "jane@example.com",
            "Welcome to ThinkWrapper Newsletter",
            html_content
        )
        
        assert result is True
        assert "Jane Doe" in html_content
    
    @patch("app.services.Client")
    @patch.dict(os.environ, {"MAILJET_API_KEY": "test-api-key", "MAILJET_API_SECRET": "test-api-secret"})
    def test_send_newsletter_email(self, mock_mailjet_client, app_context):
        """Test sending newsletter with custom template."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_send = Mock()
        mock_send.create = Mock(return_value=mock_response)
        mock_client.send = mock_send
        mock_mailjet_client.return_value = mock_client
        
        newsletter_content = """
            <h2>AI Weekly Update</h2>
            <p>Latest developments in artificial intelligence...</p>
        """
        html_content = get_newsletter_template(
            "AI Weekly Update",
            newsletter_content,
            preheader="Your weekly AI digest"
        )
        
        result = services.send_email(
            "subscriber@example.com",
            "AI Weekly Update",
            html_content
        )
        
        assert result is True
    
    @patch("app.services.Client")
    @patch.dict(os.environ, {"MAILJET_API_KEY": "test-api-key", "MAILJET_API_SECRET": "test-api-secret"})
    def test_email_failure_handling(self, mock_mailjet_client, app_context):
        """Test handling of email send failures."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 400  # Bad request
        mock_send = Mock()
        mock_send.create = Mock(return_value=mock_response)
        mock_client.send = mock_send
        mock_mailjet_client.return_value = mock_client
        
        html_content = get_test_template()
        
        result = services.send_email(
            "test@example.com",
            "Test Subject",
            html_content
        )
        
        assert result is False
    
    @patch("app.services.Client")
    @patch.dict(os.environ, {"MAILJET_API_KEY": "test-api-key", "MAILJET_API_SECRET": "test-api-secret"})
    def test_email_network_error_handling(self, mock_mailjet_client, app_context):
        """Test handling of network errors during email send."""
        mock_client = Mock()
        mock_send = Mock()
        mock_send.create = Mock(side_effect=Exception("Network error"))
        mock_client.send = mock_send
        mock_mailjet_client.return_value = mock_client
        
        html_content = get_test_template()
        
        result = services.send_email(
            "test@example.com",
            "Test Subject",
            html_content
        )
        
        assert result is False
    
    @patch.dict(os.environ, {}, clear=True)
    def test_email_missing_api_key(self, app_context):
        """Test email send fails gracefully when API key is missing."""
        html_content = get_test_template()
        
        result = services.send_email(
            "test@example.com",
            "Test Subject",
            html_content
        )
        
        assert result is False
    
    @patch.dict(os.environ, {"MAILJET_API_KEY": "test-key"}, clear=True)
    def test_email_missing_api_secret(self, app_context):
        """Test email send fails gracefully when API secret is missing."""
        html_content = get_test_template()
        
        result = services.send_email(
            "test@example.com",
            "Test Subject",
            html_content
        )
        
        assert result is False
    
    @patch("app.services.Client")
    @patch.dict(os.environ, {"MAILJET_API_KEY": "test-api-key", "MAILJET_API_SECRET": "test-api-secret"})
    def test_email_rate_limit_handling(self, mock_mailjet_client, app_context):
        """Test handling of rate limit errors."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 429  # Rate limit
        mock_send = Mock()
        mock_send.create = Mock(return_value=mock_response)
        mock_client.send = mock_send
        mock_mailjet_client.return_value = mock_client
        
        html_content = get_test_template()
        
        result = services.send_email(
            "test@example.com",
            "Test Subject",
            html_content
        )
        
        assert result is False
    
    @patch("app.services.Client")
    @patch.dict(os.environ, {"MAILJET_API_KEY": "test-api-key", "MAILJET_API_SECRET": "test-api-secret"})
    def test_email_server_error_handling(self, mock_mailjet_client, app_context):
        """Test handling of server errors."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 500  # Internal server error
        mock_send = Mock()
        mock_send.create = Mock(return_value=mock_response)
        mock_client.send = mock_send
        mock_mailjet_client.return_value = mock_client
        
        html_content = get_test_template()
        
        result = services.send_email(
            "test@example.com",
            "Test Subject",
            html_content
        )
        
        assert result is False


class TestEmailE2E:
    """End-to-end tests with real Mailjet API (requires API key and secret)."""
    
    @pytest.mark.skipif(
        not os.environ.get("MAILJET_API_KEY") or 
        not os.environ.get("MAILJET_API_SECRET"),
        reason="Real MAILJET_API_KEY and MAILJET_API_SECRET not configured"
    )
    def test_send_real_email(self, app_context):
        """
        Test sending email with real Mailjet API.
        
        This test is skipped unless real MAILJET_API_KEY and MAILJET_API_SECRET are set.
        Set MAILJET_TEST_EMAIL environment variable to your test email address.
        """
        test_email = os.environ.get("MAILJET_TEST_EMAIL", "test@example.com")
        
        html_content = get_test_template()
        
        result = services.send_email(
            test_email,
            "Test Email - Mailjet Integration",
            html_content
        )
        
        # With real API key, this should succeed
        assert result is True
    
    @pytest.mark.skipif(
        not os.environ.get("MAILJET_API_KEY") or 
        not os.environ.get("MAILJET_API_SECRET"),
        reason="Real MAILJET_API_KEY and MAILJET_API_SECRET not configured"
    )
    def test_send_welcome_email_real(self, app_context):
        """Test sending welcome email with real API."""
        test_email = os.environ.get("MAILJET_TEST_EMAIL", "test@example.com")
        
        html_content = get_welcome_template("Test User")
        
        result = services.send_email(
            test_email,
            "Welcome to ThinkWrapper Newsletter",
            html_content
        )
        
        assert result is True
    
    @pytest.mark.skipif(
        not os.environ.get("MAILJET_API_KEY") or 
        not os.environ.get("MAILJET_API_SECRET"),
        reason="Real MAILJET_API_KEY and MAILJET_API_SECRET not configured"
    )
    def test_send_newsletter_real(self, app_context):
        """Test sending newsletter email with real API."""
        test_email = os.environ.get("MAILJET_TEST_EMAIL", "test@example.com")
        
        newsletter_content = """
            <h2>Test Newsletter</h2>
            <p>This is a test newsletter to verify the Mailjet integration.</p>
            <p>If you received this, everything is working correctly!</p>
        """
        html_content = get_newsletter_template(
            "Test Newsletter",
            newsletter_content,
            preheader="Testing Mailjet integration"
        )
        
        result = services.send_email(
            test_email,
            "Test Newsletter - Mailjet Integration",
            html_content
        )
        
        assert result is True
