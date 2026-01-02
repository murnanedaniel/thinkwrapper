"""
Tests for newsletter synthesis service, rendering, and configuration.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock
from app.newsletter_synthesis import (
    NewsletterSynthesizer,
    NewsletterRenderer,
    NewsletterConfig
)


class TestNewsletterSynthesizer:
    """Test the newsletter synthesizer service."""
    
    def test_init(self):
        """Test synthesizer initialization."""
        synthesizer = NewsletterSynthesizer()
        assert synthesizer is not None
    
    def test_collect_source_content_default(self):
        """Test collecting source content with default parameters."""
        synthesizer = NewsletterSynthesizer()
        content_items = synthesizer.collect_source_content(newsletter_id=1)
        
        assert isinstance(content_items, list)
        assert len(content_items) > 0
        
        # Verify structure of content items
        for item in content_items:
            assert 'title' in item
            assert 'summary' in item
            assert 'source' in item
            assert 'created_at' in item
    
    def test_collect_source_content_with_since(self):
        """Test collecting source content with specific date."""
        synthesizer = NewsletterSynthesizer()
        since_date = datetime.utcnow() - timedelta(days=30)
        content_items = synthesizer.collect_source_content(
            newsletter_id=1,
            since=since_date
        )
        
        assert isinstance(content_items, list)
        assert len(content_items) > 0
    
    @patch('openai.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_synthesize_newsletter_success(self, mock_openai_class):
        """Test successful newsletter synthesis with OpenAI."""
        synthesizer = NewsletterSynthesizer()
        
        # Mock OpenAI client and response properly for chat completions API
        mock_client = Mock()
        mock_message = Mock()
        mock_message.content = "AI Weekly Update\n\nThis week in AI has been exciting..."
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        content_items = [
            {'title': 'AI News', 'summary': 'Latest AI developments'}
        ]
        
        result = synthesizer.synthesize_newsletter(
            topic="Artificial Intelligence",
            content_items=content_items
        )
        
        assert result is not None
        assert 'subject' in result
        assert 'content' in result
        # Mock is now properly set up for chat completions, so we get the AI-generated subject
        assert result['subject'] == "AI Weekly Update"
        assert "This week in AI" in result['content']
    
    @patch('openai.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_synthesize_newsletter_with_style(self, mock_openai_class):
        """Test newsletter synthesis with different styles."""
        synthesizer = NewsletterSynthesizer()
        
        # Mock OpenAI client properly for chat completions API
        mock_client = Mock()
        mock_message = Mock()
        mock_message.content = "Tech Brief\n\nCasual AI update..."
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        content_items = [
            {'title': 'AI News', 'summary': 'Latest AI developments'}
        ]
        
        result = synthesizer.synthesize_newsletter(
            topic="AI",
            content_items=content_items,
            style="casual"
        )
        
        assert result is not None
        # Verify style was included in the messages
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        # Check that messages contain the style
        messages = call_args['messages']
        user_message = next(m for m in messages if m['role'] == 'user')
        assert 'casual' in user_message['content']
    
    @patch('openai.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_synthesize_newsletter_openai_error(self, mock_openai_class):
        """Test fallback when OpenAI fails."""
        mock_openai_class.side_effect = Exception("API Error")
        
        synthesizer = NewsletterSynthesizer()
        content_items = [
            {'title': 'Test', 'summary': 'Test summary', 'url': 'http://test.com'}
        ]
        
        result = synthesizer.synthesize_newsletter(
            topic="Test Topic",
            content_items=content_items
        )
        
        # Should fall back to generated content
        assert result is not None
        assert 'subject' in result
        assert 'content' in result
        assert "Test Topic" in result['subject']
    
    def test_generate_fallback_content(self):
        """Test fallback content generation."""
        synthesizer = NewsletterSynthesizer()
        content_items = [
            {
                'title': 'Item 1',
                'summary': 'Summary 1',
                'url': 'http://example.com/1'
            },
            {
                'title': 'Item 2',
                'summary': 'Summary 2',
                'url': 'http://example.com/2'
            }
        ]
        
        result = synthesizer._generate_fallback_content("Tech News", content_items)
        
        assert result is not None
        assert 'subject' in result
        assert 'content' in result
        assert "Tech News" in result['subject']
        assert "Item 1" in result['content']
        assert "Item 2" in result['content']
    
    @patch('app.newsletter_synthesis.NewsletterSynthesizer.collect_source_content')
    @patch('app.newsletter_synthesis.NewsletterSynthesizer.synthesize_newsletter')
    def test_generate_on_demand_success(self, mock_synthesize, mock_collect):
        """Test on-demand newsletter generation."""
        synthesizer = NewsletterSynthesizer()
        
        # Mock data
        mock_collect.return_value = [
            {'title': 'Test', 'summary': 'Test summary'}
        ]
        mock_synthesize.return_value = {
            'subject': 'Test Subject',
            'content': 'Test content'
        }
        
        result = synthesizer.generate_on_demand(
            newsletter_id=1,
            topic="Test Topic"
        )
        
        assert result['success'] is True
        assert result['subject'] == 'Test Subject'
        assert result['content'] == 'Test content'
        assert result['content_items_count'] == 1
        assert 'generated_at' in result
        assert result['style'] == 'professional'
    
    @patch('app.newsletter_synthesis.NewsletterSynthesizer.collect_source_content')
    def test_generate_on_demand_error(self, mock_collect):
        """Test on-demand generation error handling."""
        mock_collect.side_effect = Exception("Collection failed")
        
        synthesizer = NewsletterSynthesizer()
        result = synthesizer.generate_on_demand(
            newsletter_id=1,
            topic="Test"
        )
        
        assert result['success'] is False
        assert 'error' in result
        assert 'generated_at' in result


class TestNewsletterRenderer:
    """Test newsletter rendering in different formats."""
    
    def test_render_plain_text(self):
        """Test plain text rendering."""
        renderer = NewsletterRenderer()
        content = {
            'subject': 'Test Newsletter',
            'content': '# Header\n\nThis is **bold** text.\n\n## Section\n\nMore content.'
        }
        
        result = renderer.render_plain_text(content)
        
        assert 'Test Newsletter' in result
        assert 'Header' in result
        assert 'bold' in result
        assert '=' in result  # Separator lines
    
    def test_render_html(self):
        """Test HTML rendering."""
        renderer = NewsletterRenderer()
        content = {
            'subject': 'HTML Newsletter',
            'content': '# Main Title\n\nParagraph text.\n\n## Subtitle\n\nMore text.'
        }
        
        result = renderer.render_html(content)
        
        assert '<!DOCTYPE html>' in result
        assert 'HTML Newsletter' in result
        assert '<h1>' in result
        assert '<h2>' in result
        assert '<p>' in result
        assert 'style' in result.lower()  # CSS included
    
    def test_render_html_with_links(self):
        """Test HTML rendering preserves structure."""
        renderer = NewsletterRenderer()
        content = {
            'subject': 'Newsletter',
            'content': 'Check this out.\n\n### Subheading\n\nContent here.'
        }
        
        result = renderer.render_html(content)
        
        assert '<h3>' in result
        assert '</h3>' in result
    
    def test_markdown_to_html_headers(self):
        """Test markdown header conversion."""
        renderer = NewsletterRenderer()
        markdown = "# H1\n## H2\n### H3"
        
        result = renderer._markdown_to_html(markdown)
        
        assert '<h1>H1</h1>' in result
        assert '<h2>H2</h2>' in result
        assert '<h3>H3</h3>' in result
    
    def test_markdown_to_html_paragraphs(self):
        """Test paragraph conversion."""
        renderer = NewsletterRenderer()
        markdown = "First paragraph.\n\nSecond paragraph."
        
        result = renderer._markdown_to_html(markdown)
        
        assert '<p>' in result
        assert '</p>' in result
    
    def test_render_with_format_html(self):
        """Test render method with HTML format."""
        renderer = NewsletterRenderer()
        content = {'subject': 'Test', 'content': 'Content'}
        
        result = renderer.render(content, format="html")
        
        assert '<!DOCTYPE html>' in result
    
    def test_render_with_format_text(self):
        """Test render method with text format."""
        renderer = NewsletterRenderer()
        content = {'subject': 'Test', 'content': 'Content'}
        
        result = renderer.render(content, format="text")
        
        assert 'Subject: Test' in result
        assert '=' in result
    
    def test_render_default_format(self):
        """Test render method defaults to HTML."""
        renderer = NewsletterRenderer()
        content = {'subject': 'Test', 'content': 'Content'}
        
        result = renderer.render(content)
        
        assert '<!DOCTYPE html>' in result


class TestNewsletterConfig:
    """Test newsletter configuration management."""
    
    def test_init_defaults(self):
        """Test default configuration values."""
        config = NewsletterConfig()
        
        assert config.schedule == "weekly"
        assert config.delivery_format == "html"
        assert config.max_content_items == 10
        assert config.style == "professional"
        assert config.send_time == "09:00"
        assert config.timezone == "UTC"
    
    def test_from_dict(self):
        """Test loading configuration from dictionary."""
        config = NewsletterConfig()
        config_data = {
            'schedule': 'daily',
            'delivery_format': 'text',
            'style': 'casual'
        }
        
        config.from_dict(config_data)
        
        assert config.schedule == 'daily'
        assert config.delivery_format == 'text'
        assert config.style == 'casual'
    
    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        config = NewsletterConfig()
        config.schedule = 'monthly'
        
        result = config.to_dict()
        
        assert isinstance(result, dict)
        assert result['schedule'] == 'monthly'
        assert 'delivery_format' in result
        assert 'style' in result
    
    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = NewsletterConfig()
        
        is_valid, error = config.validate()
        
        assert is_valid is True
        assert error is None
    
    def test_validate_invalid_schedule(self):
        """Test validation with invalid schedule."""
        config = NewsletterConfig()
        config.schedule = 'invalid_schedule'
        
        is_valid, error = config.validate()
        
        assert is_valid is False
        assert 'schedule' in error.lower()
    
    def test_validate_invalid_format(self):
        """Test validation with invalid format."""
        config = NewsletterConfig()
        config.delivery_format = 'pdf'
        
        is_valid, error = config.validate()
        
        assert is_valid is False
        assert 'format' in error.lower()
    
    def test_validate_invalid_style(self):
        """Test validation with invalid style."""
        config = NewsletterConfig()
        config.style = 'unknown'
        
        is_valid, error = config.validate()
        
        assert is_valid is False
        assert 'style' in error.lower()
    
    def test_validate_invalid_max_items(self):
        """Test validation with invalid max_content_items."""
        config = NewsletterConfig()
        config.max_content_items = 0
        
        is_valid, error = config.validate()
        
        assert is_valid is False
        assert 'max_content_items' in error.lower()
    
    def test_validate_max_items_too_high(self):
        """Test validation with too many max_content_items."""
        config = NewsletterConfig()
        config.max_content_items = 100
        
        is_valid, error = config.validate()
        
        assert is_valid is False
        assert 'max_content_items' in error.lower()
    
    def test_from_dict_ignores_unknown_fields(self):
        """Test that from_dict ignores unknown fields."""
        config = NewsletterConfig()
        config_data = {
            'schedule': 'daily',
            'unknown_field': 'should_be_ignored'
        }
        
        config.from_dict(config_data)
        
        assert config.schedule == 'daily'
        assert not hasattr(config, 'unknown_field')


class TestNewsletterIntegration:
    """Integration tests for newsletter synthesis workflow."""
    
    @patch('openai.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_full_synthesis_and_render_workflow(self, mock_openai_class):
        """Test complete workflow from synthesis to rendering."""
        # Setup - mock OpenAI properly for chat completions API
        mock_client = Mock()
        mock_message = Mock()
        mock_message.content = "Newsletter Title\n\nNewsletter content here."
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        synthesizer = NewsletterSynthesizer()
        renderer = NewsletterRenderer()
        
        # Collect and synthesize
        content_items = synthesizer.collect_source_content(newsletter_id=1)
        synthesized = synthesizer.synthesize_newsletter(
            topic="Tech Weekly",
            content_items=content_items
        )
        
        # Render in both formats
        html_output = renderer.render_html(synthesized)
        text_output = renderer.render_plain_text(synthesized)
        
        # Verify
        assert synthesized is not None
        assert html_output is not None
        assert text_output is not None
        assert '<!DOCTYPE html>' in html_output
        # With proper mocking, the title is now correctly generated
        assert 'Newsletter Title' in text_output
    
    def test_config_workflow(self):
        """Test configuration create, validate, update workflow."""
        config = NewsletterConfig()
        
        # Validate defaults
        is_valid, error = config.validate()
        assert is_valid is True
        
        # Update configuration
        new_config = {
            'schedule': 'monthly',
            'style': 'technical'
        }
        config.from_dict(new_config)
        
        # Validate updated config
        is_valid, error = config.validate()
        assert is_valid is True
        assert config.schedule == 'monthly'
        
        # Export to dict
        exported = config.to_dict()
        assert exported['schedule'] == 'monthly'
        assert exported['style'] == 'technical'
