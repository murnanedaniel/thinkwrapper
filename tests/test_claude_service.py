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
    def __init__(self, text, model="claude-haiku-4-5", stop_reason="end_turn"):
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
        assert result['model'] == "claude-haiku-4-5"
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
        assert result['model'] == "claude-haiku-4-5"
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
        assert result['model'] == "claude-haiku-4-5"
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
            model="claude-haiku-4-5",
            max_tokens=300,
            temperature=0.8,
            system_prompt="System context"
        )
        
        assert result is not None
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs['model'] == "claude-haiku-4-5"
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


class TestNewsletterWithSearch:
    """Test newsletter generation with Brave Search integration."""
    
    @patch('app.claude_service._get_client')
    @patch('app.services.search_brave')
    def test_generate_newsletter_with_search_success(self, mock_search_brave, mock_get_client):
        """Test successful newsletter generation with real search results."""
        # Mock search results
        mock_search_results = {
            'success': True,
            'source': 'brave',
            'query': 'AI trends',
            'results': [
                {
                    'title': 'Latest AI Developments',
                    'url': 'https://example.com/ai-developments',
                    'description': 'Recent breakthroughs in artificial intelligence'
                },
                {
                    'title': 'Machine Learning News',
                    'url': 'https://example.com/ml-news',
                    'description': 'Latest updates in machine learning'
                }
            ],
            'total_results': 2
        }
        mock_search_brave.return_value = mock_search_results
        
        # Mock Claude response with real URLs
        mock_client = Mock()
        content = """Subject: AI Trends Weekly Update

Check out these fascinating articles:

1. Latest AI Developments - https://example.com/ai-developments
Recent breakthroughs in artificial intelligence are changing the landscape.

2. Machine Learning News - https://example.com/ml-news
Stay updated with the latest in machine learning."""
        mock_message = MockMessage(content)
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_newsletter_with_search("AI trends")
        
        assert result is not None
        assert 'subject' in result
        assert 'content' in result
        assert 'articles' in result
        assert 'search_source' in result
        assert 'total_articles' in result
        
        # Verify real URLs are in the content
        assert 'https://example.com/ai-developments' in result['content']
        assert 'https://example.com/ml-news' in result['content']
        
        # Verify articles are included
        assert len(result['articles']) == 2
        assert result['articles'][0]['url'] == 'https://example.com/ai-developments'
        assert result['search_source'] == 'brave'
        assert result['total_articles'] == 2
        
        # Verify search was called
        mock_search_brave.assert_called_once_with(query='AI trends', count=10, fallback_to_mock=True)
        
        # Verify Claude was called with article data in prompt
        call_kwargs = mock_client.messages.create.call_args[1]
        prompt_content = call_kwargs['messages'][0]['content']
        assert 'Latest AI Developments' in prompt_content
        assert 'https://example.com/ai-developments' in prompt_content
    
    def test_sanitize_text_for_prompt(self):
        """Test text sanitization for prompt injection prevention."""
        # Test basic sanitization
        result = claude_service._sanitize_text_for_prompt("Normal text")
        assert result == "Normal text"
        
        # Test newline removal
        result = claude_service._sanitize_text_for_prompt("Text with\nnewlines\r\nhere")
        assert '\n' not in result
        assert '\r' not in result
        assert result == "Text with newlines here"
        
        # Test multiple space normalization
        result = claude_service._sanitize_text_for_prompt("Text   with    spaces")
        assert result == "Text with spaces"
        
        # Test length limiting
        long_text = "a" * 600
        result = claude_service._sanitize_text_for_prompt(long_text)
        assert len(result) <= 503  # 500 + "..."
        assert result.endswith("...")
        
        # Test empty string
        result = claude_service._sanitize_text_for_prompt("")
        assert result == ""
        
        # Test None handling
        result = claude_service._sanitize_text_for_prompt(None)
        assert result == ""
    
    @patch('app.claude_service._get_client')
    @patch('app.services.search_brave')
    def test_generate_newsletter_with_search_sanitizes_articles(self, mock_search_brave, mock_get_client):
        """Test that article data is sanitized before being used in prompt."""
        # Mock search results with potentially malicious content
        mock_search_results = {
            'success': True,
            'source': 'brave',
            'query': 'test',
            'results': [
                {
                    'title': 'Title with\nnewlines\nhere',
                    'url': 'https://example.com',
                    'description': 'Description   with   spaces'
                }
            ],
            'total_results': 1
        }
        mock_search_brave.return_value = mock_search_results
        
        mock_client = Mock()
        mock_message = MockMessage("Subject: Test\n\nContent")
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_newsletter_with_search("test")
        
        assert result is not None
        
        # Verify prompt was sanitized
        call_kwargs = mock_client.messages.create.call_args[1]
        prompt_content = call_kwargs['messages'][0]['content']
        
        # Newlines should be removed from title
        assert 'Title with\nnewlines' not in prompt_content
        assert 'Title with newlines here' in prompt_content
        
        # Multiple spaces should be normalized in description
        assert 'Description   with   spaces' not in prompt_content
        assert 'Description with spaces' in prompt_content
    
    @patch('app.claude_service._get_client')
    @patch('app.services.search_brave')
    def test_generate_newsletter_with_search_custom_count(self, mock_search_brave, mock_get_client):
        """Test newsletter generation with custom search count."""
        mock_search_results = {
            'success': True,
            'source': 'brave',
            'results': [{'title': 'Test', 'url': 'https://test.com', 'description': 'Test'}],
            'total_results': 1
        }
        mock_search_brave.return_value = mock_search_results
        
        mock_client = Mock()
        mock_message = MockMessage("Subject: Test\n\nContent with https://test.com")
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_newsletter_with_search("Topic", search_count=5)
        
        assert result is not None
        mock_search_brave.assert_called_once_with(query='Topic', count=5, fallback_to_mock=True)
    
    @patch('app.claude_service._get_client')
    @patch('app.services.search_brave')
    def test_generate_newsletter_with_search_no_results(self, mock_search_brave, mock_get_client):
        """Test newsletter generation when search returns no results."""
        mock_search_results = {
            'success': False,
            'source': 'brave',
            'results': [],
            'total_results': 0,
            'error': 'No results found'
        }
        mock_search_brave.return_value = mock_search_results
        
        result = claude_service.generate_newsletter_with_search("Obscure Topic")
        
        assert result is None
    
    @patch('app.claude_service._get_client')
    @patch('app.services.search_brave')
    def test_generate_newsletter_with_search_mock_fallback(self, mock_search_brave, mock_get_client):
        """Test newsletter generation with mock search fallback."""
        mock_search_results = {
            'success': True,
            'source': 'mock',
            'query': 'Test Topic',
            'results': [
                {
                    'title': 'Mock Result 1 for "Test Topic"',
                    'url': 'https://example.com/result/1',
                    'description': 'This is a mock search result'
                }
            ],
            'total_results': 1
        }
        mock_search_brave.return_value = mock_search_results
        
        mock_client = Mock()
        mock_message = MockMessage("Subject: Test\n\nContent with https://example.com/result/1")
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_newsletter_with_search("Test Topic")
        
        assert result is not None
        assert result['search_source'] == 'mock'
        assert 'https://example.com/result/1' in result['content']
    
    @patch('app.claude_service._get_client')
    @patch('app.services.search_brave')
    def test_generate_newsletter_with_search_no_api_key(self, mock_search_brave, mock_get_client):
        """Test newsletter generation when Claude API key is not configured."""
        mock_search_results = {
            'success': True,
            'source': 'brave',
            'results': [{'title': 'Test', 'url': 'https://test.com', 'description': 'Test'}],
            'total_results': 1
        }
        mock_search_brave.return_value = mock_search_results
        mock_get_client.return_value = None
        
        result = claude_service.generate_newsletter_with_search("Topic")
        
        assert result is None
    
    @patch('app.claude_service._get_client')
    @patch('app.services.search_brave')
    def test_generate_newsletter_with_search_includes_style(self, mock_search_brave, mock_get_client):
        """Test that style parameter is passed to the prompt."""
        mock_search_results = {
            'success': True,
            'source': 'brave',
            'results': [{'title': 'Test', 'url': 'https://test.com', 'description': 'Test'}],
            'total_results': 1
        }
        mock_search_brave.return_value = mock_search_results
        
        mock_client = Mock()
        mock_message = MockMessage("Subject: Technical Brief\n\nDetailed content")
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_newsletter_with_search("Topic", style="technical")
        
        assert result is not None
        call_kwargs = mock_client.messages.create.call_args[1]
        prompt_content = call_kwargs['messages'][0]['content']
        assert 'technical' in prompt_content
    
    @patch('app.claude_service._get_client')
    @patch('app.services.search_brave')
    def test_generate_newsletter_with_search_real_urls_only(self, mock_search_brave, mock_get_client):
        """Test that the prompt emphasizes using only real URLs."""
        mock_search_results = {
            'success': True,
            'source': 'brave',
            'results': [{'title': 'Test', 'url': 'https://real-url.com', 'description': 'Test'}],
            'total_results': 1
        }
        mock_search_brave.return_value = mock_search_results
        
        mock_client = Mock()
        mock_message = MockMessage("Subject: Test\n\nContent")
        mock_client.messages.create.return_value = mock_message
        mock_get_client.return_value = mock_client
        
        result = claude_service.generate_newsletter_with_search("Topic")
        
        # Verify the prompt emphasizes real URLs
        call_kwargs = mock_client.messages.create.call_args[1]
        prompt_content = call_kwargs['messages'][0]['content']
        assert 'REAL URLs' in prompt_content or 'real URLs' in prompt_content
        assert 'not placeholder' in prompt_content or 'Do not make up' in prompt_content
        
        # Verify system prompt reinforces real URLs
        system_prompt = call_kwargs.get('system', '')
        assert 'real' in system_prompt.lower()
        assert 'never make up' in system_prompt.lower() or 'must use only' in system_prompt.lower()
