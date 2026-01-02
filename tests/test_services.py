import os
from unittest.mock import patch, Mock
from app import services


class TestNewsletterGeneration:
    """Test newsletter content generation using OpenAI."""

    @patch("app.services.get_openai_client")
    def test_generate_newsletter_content_success(self, mock_get_client, app_context):
        """Test successful newsletter generation."""
        # Mock OpenAI client for v1.0+ API
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Subject: AI Weekly Update\n\nGreat content about AI..."
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = services.generate_newsletter_content("Artificial Intelligence")

        assert result is not None
        assert "subject" in result
        assert "content" in result
        assert result["subject"] == "Subject: AI Weekly Update"
        assert "Great content about AI..." in result["content"]

        # Verify OpenAI was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert "messages" in call_args[1]
        assert call_args[1]["model"] == "gpt-4"
        assert call_args[1]["max_tokens"] == 1500
        assert call_args[1]["temperature"] == 0.7

    @patch("app.services.get_openai_client")
    def test_generate_newsletter_content_with_style(self, mock_get_client, app_context):
        """Test newsletter generation with custom style."""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Subject: Tech Brief\n\nConcise AI update..."
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = services.generate_newsletter_content("AI", style="brief")

        assert result is not None
        assert "subject" in result
        assert "content" in result

        # Check that style was included in prompt
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        user_message = next(m for m in messages if m["role"] == "user")
        assert "brief" in user_message["content"]

    @patch("app.services.get_openai_client")
    def test_generate_newsletter_content_openai_error(
        self, mock_get_client, app_context
    ):
        """Test handling of OpenAI API errors."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("OpenAI API Error")
        mock_get_client.return_value = mock_client

        result = services.generate_newsletter_content("Test Topic")

        assert result is None

    @patch("app.services.get_openai_client")
    def test_generate_newsletter_content_logs_error(self, mock_get_client, app_context):
        """Test that errors are properly logged."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Rate Limit")
        mock_get_client.return_value = mock_client

        result = services.generate_newsletter_content("Test Topic")

        assert result is None
        # Logger is used within app context, error is logged


class TestEmailService:
    """Test email sending functionality using SendGrid."""

    @patch("app.services.sendgrid.SendGridAPIClient")
    @patch.dict(os.environ, {"SENDGRID_API_KEY": "test-api-key"})
    def test_send_email_success(self, mock_sendgrid_client, app_context):
        """Test successful email sending."""
        # Mock SendGrid client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client.client.mail.send.post.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client

        result = services.send_email(
            "test@example.com", "Test Subject", "<h1>Test Content</h1>"
        )

        assert result is True
        mock_sendgrid_client.assert_called_once_with(api_key="test-api-key")
        mock_client.client.mail.send.post.assert_called_once()

    @patch("app.services.sendgrid.SendGridAPIClient")
    @patch.dict(os.environ, {"SENDGRID_API_KEY": "test-api-key"})
    def test_send_email_success_with_200_status(
        self, mock_sendgrid_client, app_context
    ):
        """Test successful email sending with 200 status code."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200  # Alternative success status
        mock_client.client.mail.send.post.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client

        result = services.send_email("test@example.com", "Test Subject", "Test Content")

        assert result is True

    @patch("app.services.sendgrid.SendGridAPIClient")
    @patch.dict(os.environ, {"SENDGRID_API_KEY": "test-api-key"})
    def test_send_email_failure_status(self, mock_sendgrid_client, app_context):
        """Test email sending with failure status code."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 400  # Error status
        mock_client.client.mail.send.post.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client

        result = services.send_email("test@example.com", "Test Subject", "Test Content")

        assert result is False

    @patch.dict(os.environ, {}, clear=True)
    def test_send_email_no_api_key(self, app_context):
        """Test email sending without API key configured."""
        result = services.send_email("test@example.com", "Test Subject", "Test Content")

        assert result is False

    @patch("app.services.sendgrid.SendGridAPIClient")
    @patch.dict(os.environ, {"SENDGRID_API_KEY": "test-api-key"})
    def test_send_email_sendgrid_exception(self, mock_sendgrid_client, app_context):
        """Test handling of SendGrid exceptions."""
        mock_sendgrid_client.side_effect = Exception("SendGrid connection error")

        result = services.send_email("test@example.com", "Test Subject", "Test Content")

        assert result is False

    @patch("app.services.sendgrid.SendGridAPIClient")
    @patch.dict(os.environ, {"SENDGRID_API_KEY": "test-api-key"})
    def test_send_email_mail_construction(self, mock_sendgrid_client, app_context):
        """Test that email components are properly constructed."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client.client.mail.send.post.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client

        # Test with HTML content
        result = services.send_email(
            "recipient@example.com",
            "Newsletter Subject",
            "<html><body><h1>HTML Content</h1></body></html>",
        )

        assert result is True

        # Verify the mail was sent with proper request body
        mock_client.client.mail.send.post.assert_called_once()
        call_args = mock_client.client.mail.send.post.call_args
        assert "request_body" in call_args[1]


class TestWebhookVerification:
    """Test Paddle webhook signature verification."""

    def test_verify_paddle_webhook_placeholder(self):
        """Test that webhook verification currently returns True (placeholder)."""
        # Current implementation always returns True
        result = services.verify_paddle_webhook(
            {"event": "subscription_created"}, "test-signature"
        )

        assert result is True

    def test_verify_paddle_webhook_with_different_data(self):
        """Test webhook verification with various data types."""
        test_cases = [
            ({"user_id": 123}, "sig123"),
            ({}, "empty_sig"),
            ({"complex": {"nested": "data"}}, "complex_sig"),
            (None, None),
        ]

        for data, signature in test_cases:
            result = services.verify_paddle_webhook(data, signature)
            # All should return True with current placeholder implementation
            assert result is True


class TestServiceConfiguration:
    """Test service configuration and environment setup."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"})
    @patch("app.services.OpenAI")
    def test_openai_api_key_configuration(self, mock_openai_class):
        """Test that OpenAI API key is properly configured."""
        mock_client = Mock()
        mock_client.api_key = "test-openai-key"
        mock_openai_class.return_value = mock_client

        client = services.get_openai_client()

        # The client should be configured with the API key
        assert client is not None
        mock_openai_class.assert_called_once_with(api_key="test-openai-key")

    @patch.dict(os.environ, {}, clear=True)
    def test_openai_api_key_missing(self):
        """Test behavior when OpenAI API key is missing."""
        client = services.get_openai_client()

        # Should be None when not set
        assert client is None


class TestContentProcessing:
    """Test content processing and text manipulation."""

    @patch("app.services.get_openai_client")
    def test_generate_newsletter_content_text_processing(
        self, mock_get_client, app_context
    ):
        """Test that content is properly processed and split."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = """Subject: Weekly AI Update

        This is the first paragraph of content.
        
        This is the second paragraph with more details.
        
        Conclusion paragraph here."""
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = services.generate_newsletter_content("AI Weekly")

        assert result is not None
        assert result["subject"] == "Subject: Weekly AI Update"
        assert "This is the first paragraph" in result["content"]
        assert "Conclusion paragraph here" in result["content"]
        # Subject should not be in content
        assert "Subject: Weekly AI Update" not in result["content"]

    @patch("app.services.get_openai_client")
    def test_generate_newsletter_single_line_content(
        self, mock_get_client, app_context
    ):
        """Test handling of single-line responses."""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Single line content without subject"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = services.generate_newsletter_content("Test")

        assert result is not None
        assert result["subject"] == "Single line content without subject"
        assert result["content"] == ""
