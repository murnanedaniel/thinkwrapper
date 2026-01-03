"""
Tests for Claude API Service Module

This module contains comprehensive tests for the Claude API integration,
including both synchronous and asynchronous functionality.
"""

import pytest
import os
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from app import claude_service
from anthropic.types import Message, Usage, ContentBlock, TextBlock


class MockTextBlock:
    """Mock for Anthropic TextBlock."""
    def __init__(self, text):
        self.text = text
        self.type = "text"


class MockMessage:
    """Mock for Anthropic Message response."""
    def __init__(self, text, model="claude-3-haiku-20240307", stop_reason="end_turn"):
        self.content = [MockTextBlock(text)]
        self.model = model
        self.usage = Usage(input_tokens=10, output_tokens=100)
        self.stop_reason = stop_reason
        self.id = "msg_test_123"


class TestPromptFormatting:
    """Test prompt formatting utilities."""
    
    def test_format_prompt_basic(self):
        """Test basic prompt formatting."""
        result = claude_service.format_prompt("AI trends")
        assert "AI trends" in result
        assert isinstance(result, str)
    
    def test_format_prompt_with_style(self):
        """Test prompt formatting with style."""
        result = claude_service.format_prompt("Machine Learning", style="technical")
        assert "Machine Learning" in result
        assert "technical" in result
    
    def test_format_prompt_with_length(self):
        """Test prompt formatting with max_length."""
        result = claude_service.format_prompt("Python", max_length="brief")
        assert "Python" in result
        assert "brief" in result
    
    def test_format_prompt_with_context(self):
        """Test prompt formatting with additional context."""
        result = claude_service.format_prompt(
            "Data Science",
            additional_context="Focus on 2024 trends"
        )
        assert "Data Science" in result
        assert "2024 trends" in result
    
    def test_format_prompt_all_parameters(self):
        """Test prompt formatting with all parameters."""
        result = claude_service.format_prompt(
            topic="Quantum Computing",
            style="academic",
            max_length="comprehensive",
            additional_context="Include recent breakthroughs"
        )
        assert "Quantum Computing" in result
        assert "academic" in result
        assert "comprehensive" in result
        assert "recent breakthroughs" in result


class TestResponseParsing:
    """Test response parsing utilities."""
    
    def test_parse_response_success(self):
        """Test successful response parsing."""
        mock_message = MockMessage("This is test content")
        result = claude_service.parse_response(mock_message)
        
        assert result is not None
        assert 'text' in result
        assert 'model' in result
        assert 'usage' in result
        assert 'stop_reason' in result
        assert 'id' in result
        assert result['text'] == "This is test content"
        assert result['model'] == "claude-3-haiku-20240307"
        assert result['usage']['input_tokens'] == 10
        assert result['usage']['output_tokens'] == 100
    
    def test_parse_response_empty_content(self):
        """Test parsing response with empty content."""
        mock_message = MockMessage("")
        result = claude_service.parse_response(mock_message)
        
        assert result is not None
        assert result['text'] == ""
    
    def test_parse_response_multiline_content(self):
        """Test parsing response with multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        mock_message = MockMessage(content)
        result = claude_service.parse_response(mock_message)
        
        assert result['text'] == content
        assert "Line 1" in result['text']
        assert "Line 3" in result['text']


class TestSyncTextGeneration:
    """Test synchronous text generation."""
    
    @patch('app.claude_service._get_client')
    def test_generate_text_success(self, mock_get_client):
        """Test successful text generation."""
        mock_client = Mock()
        mock_message = MockMessage("Generated text content")
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_text("Test prompt")
        
        assert result is not None
        assert result['text'] == "Generated text content"
        assert result['model'] == "claude-3-haiku-20240307"
        mock_client.messages.create.assert_called_once()
    
    @patch('app.claude_service._get_client')
    def test_generate_text_with_parameters(self, mock_get_client):
        """Test text generation with custom parameters."""
        mock_client = Mock()
        mock_message = MockMessage("Custom response")
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_text(
            prompt="Custom prompt",
            model="claude-3-opus-20240229",
            max_tokens=500,
            temperature=0.5,
            system_prompt="You are a helpful assistant"
        )
        
        assert result is not None
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs['model'] == "claude-3-opus-20240229"
        assert call_kwargs['max_tokens'] == 500
        assert call_kwargs['temperature'] == 0.5
        assert call_kwargs['system'] == "You are a helpful assistant"
    
    @patch('app.claude_service._get_client')
    def test_generate_text_no_api_key(self, mock_get_client):
        """Test text generation without API key."""
        mock_get_client.return_value = None
        
        result = claude_service.generate_text("Test prompt")
        
        assert result is None
    
    @patch('app.claude_service._get_client')
    def test_generate_text_api_error(self, mock_get_client):
        """Test handling of API errors."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client
        
        # Call without Flask context - should still handle error gracefully
        result = claude_service.generate_text("Test prompt")
        
        assert result is None
    
    @patch('app.claude_service._get_client')
    def test_generate_text_without_system_prompt(self, mock_get_client):
        """Test that messages are created without system parameter when not provided."""
        mock_client = Mock()
        mock_message = MockMessage("Response")
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_text("Test")
        
        call_kwargs = mock_client.messages.create.call_args[1]
        assert 'system' not in call_kwargs


class TestAsyncTextGeneration:
    """Test asynchronous text generation."""
    
    @pytest.mark.asyncio
    @patch('app.claude_service._get_async_client')
    async def test_generate_text_async_success(self, mock_get_client):
        """Test successful async text generation."""
        mock_client = Mock()
        mock_message = MockMessage("Async generated text")
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        mock_get_client.return_value = mock_client
        
        result = await claude_service.generate_text_async("Test prompt")
        
        assert result is not None
        assert result['text'] == "Async generated text"
        assert result['model'] == "claude-3-haiku-20240307"
        mock_client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.claude_service._get_async_client')
    async def test_generate_text_async_with_parameters(self, mock_get_client):
        """Test async text generation with custom parameters."""
        mock_client = Mock()
        mock_message = MockMessage("Custom async response")
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        mock_get_client.return_value = mock_client
        
        result = await claude_service.generate_text_async(
            prompt="Async prompt",
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.8,
            system_prompt="System context"
        )
        
        assert result is not None
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs['model'] == "claude-3-haiku-20240307"
        assert call_kwargs['max_tokens'] == 300
        assert call_kwargs['temperature'] == 0.8
        assert call_kwargs['system'] == "System context"
    
    @pytest.mark.asyncio
    @patch('app.claude_service._get_async_client')
    async def test_generate_text_async_no_api_key(self, mock_get_client):
        """Test async text generation without API key."""
        mock_get_client.return_value = None
        
        result = await claude_service.generate_text_async("Test prompt")
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch('app.claude_service._get_async_client')
    async def test_generate_text_async_api_error(self, mock_get_client):
        """Test handling of async API errors."""
        mock_client = Mock()
        mock_client.messages.create = AsyncMock(side_effect=Exception("Async API Error"))
        mock_get_client.return_value = mock_client
        
        # Call without Flask context - should still handle error gracefully
        result = await claude_service.generate_text_async("Test prompt")
        
        assert result is None


class TestNewsletterGeneration:
    """Test newsletter-specific content generation."""
    
    @patch('app.claude_service._get_client')
    def test_generate_newsletter_content_claude_success(self, mock_get_client):
        """Test successful newsletter generation."""
        mock_client = Mock()
        content = "Subject: Weekly AI Update\n\nThis is the newsletter body with great content..."
        mock_message = MockMessage(content)
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_newsletter_content_claude("AI trends")
        
        assert result is not None
        assert 'subject' in result
        assert 'content' in result
        assert 'model' in result
        assert 'usage' in result
        assert result['subject'] == "Weekly AI Update"
        assert "newsletter body" in result['content']
        mock_client.messages.create.assert_called_once()
    
    @patch('app.claude_service._get_client')
    def test_generate_newsletter_content_with_style(self, mock_get_client):
        """Test newsletter generation with custom style."""
        mock_client = Mock()
        content = "Subject: Technical Brief\n\nDetailed technical content..."
        mock_message = MockMessage(content)
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_newsletter_content_claude(
            "Machine Learning",
            style="technical"
        )
        
        assert result is not None
        call_kwargs = mock_client.messages.create.call_args[1]
        # Verify the style was included in the prompt
        assert 'technical' in str(call_kwargs['messages'][0]['content'])
    
    @patch('app.claude_service._get_client')
    def test_generate_newsletter_content_with_max_tokens(self, mock_get_client):
        """Test newsletter generation with custom max_tokens."""
        mock_client = Mock()
        content = "Subject: Newsletter\n\nContent here..."
        mock_message = MockMessage(content)
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_newsletter_content_claude(
            "Topic",
            max_tokens=1500
        )
        
        assert result is not None
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs['max_tokens'] == 1500
    
    @patch('app.claude_service._get_client')
    def test_generate_newsletter_content_no_api_key(self, mock_get_client):
        """Test newsletter generation without API key."""
        mock_get_client.return_value = None
        
        result = claude_service.generate_newsletter_content_claude("Test Topic")
        
        assert result is None
    
    @patch('app.claude_service._get_client')
    def test_generate_newsletter_content_parsing(self, mock_get_client):
        """Test proper parsing of subject and body."""
        mock_client = Mock()
        content = "Subject: Amazing Newsletter Title\n\nFirst paragraph.\n\nSecond paragraph.\n\nConclusion."
        mock_message = MockMessage(content)
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_newsletter_content_claude("Test")
        
        assert result is not None
        assert result['subject'] == "Amazing Newsletter Title"
        assert "First paragraph" in result['content']
        assert "Conclusion" in result['content']
        # Subject should not be in content
        assert "Subject:" not in result['content']
    
    @patch('app.claude_service._get_client')
    def test_generate_newsletter_system_prompt(self, mock_get_client):
        """Test that newsletter generation uses a system prompt."""
        mock_client = Mock()
        mock_message = MockMessage("Subject: Test\n\nContent")
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_newsletter_content_claude("Topic")
        
        call_kwargs = mock_client.messages.create.call_args[1]
        assert 'system' in call_kwargs
        assert 'newsletter writer' in call_kwargs['system'].lower()


class TestAPIKeyConfiguration:
    """Test API key configuration and client initialization."""
    
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-api-key'})
    def test_get_api_key_configured(self):
        """Test getting API key when configured."""
        api_key = claude_service._get_api_key()
        assert api_key == 'test-api-key'
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_api_key_not_configured(self):
        """Test getting API key when not configured."""
        api_key = claude_service._get_api_key()
        assert api_key is None
    
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    @patch('app.claude_service.Anthropic')
    def test_get_client_success(self, mock_anthropic):
        """Test getting sync client with valid API key."""
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        client = claude_service._get_client()
        
        assert client is not None
        mock_anthropic.assert_called_once_with(api_key='test-key')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_client_no_api_key(self):
        """Test getting sync client without API key."""
        client = claude_service._get_client()
        assert client is None
    
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'async-test-key'})
    @patch('app.claude_service.AsyncAnthropic')
    def test_get_async_client_success(self, mock_async_anthropic):
        """Test getting async client with valid API key."""
        mock_client = Mock()
        mock_async_anthropic.return_value = mock_client
        
        client = claude_service._get_async_client()
        
        assert client is not None
        mock_async_anthropic.assert_called_once_with(api_key='async-test-key')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_async_client_no_api_key(self):
        """Test getting async client without API key."""
        client = claude_service._get_async_client()
        assert client is None
