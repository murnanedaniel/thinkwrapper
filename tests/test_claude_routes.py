"""
Tests for Claude API Routes

This module contains tests for the Flask routes that expose Claude API functionality.
"""

import pytest
from unittest.mock import patch, Mock
from app import create_app


@pytest.fixture
def client():
    """Create a test client for the app."""
    app = create_app({'TESTING': True})
    with app.test_client() as client:
        yield client



class TestClaudeNewsletterEndpoint:
    """Test /api/claude/newsletter endpoint."""
    
    @patch('app.claude_service.generate_newsletter_with_search')
    def test_claude_newsletter_with_search_success(self, mock_generate, client):
        """Test successful newsletter generation with search integration via API."""
        mock_generate.return_value = {
            'subject': 'Weekly AI Newsletter',
            'content': 'This week in AI... https://example.com/article1',
            'articles': [
                {'title': 'Article 1', 'url': 'https://example.com/article1', 'description': 'Test'}
            ],
            'search_source': 'brave',
            'total_articles': 1,
            'model': 'claude-haiku-4-5',
            'usage': {'input_tokens': 30, 'output_tokens': 200}
        }
        
        response = client.post('/api/claude/newsletter', json={
            'topic': 'AI trends'
        })
        
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert data['data']['subject'] == 'Weekly AI Newsletter'
        assert 'https://example.com/article1' in data['data']['content']
        assert data['data']['model'] == 'claude-haiku-4-5'
        assert 'articles' in data['data']
        assert 'search_source' in data['data']
        assert data['data']['search_source'] == 'brave'
        assert 'usage' in data['data']
        mock_generate.assert_called_once()
    
    @patch('app.claude_service.generate_newsletter_with_search')
    def test_claude_newsletter_with_search_style(self, mock_generate, client):
        """Test newsletter generation with custom style and search."""
        mock_generate.return_value = {
            'subject': 'Technical Brief',
            'content': 'Technical content... https://tech.example.com',
            'articles': [{'title': 'Tech', 'url': 'https://tech.example.com', 'description': 'Tech'}],
            'search_source': 'brave',
            'total_articles': 1,
            'model': 'claude-haiku-4-5',
            'usage': {'input_tokens': 25, 'output_tokens': 150}
        }
        
        response = client.post('/api/claude/newsletter', json={
            'topic': 'Machine Learning',
            'style': 'technical'
        })
        
        assert response.status_code == 200
        mock_generate.assert_called_once_with(
            topic='Machine Learning',
            style='technical',
            max_tokens=2000,
            search_count=10
        )
    
    @patch('app.claude_service.generate_newsletter_with_search')
    def test_claude_newsletter_with_custom_search_count(self, mock_generate, client):
        """Test newsletter generation with custom search count."""
        mock_generate.return_value = {
            'subject': 'Newsletter',
            'content': 'Content...',
            'articles': [],
            'search_source': 'brave',
            'total_articles': 0,
            'model': 'claude-haiku-4-5',
            'usage': {'input_tokens': 20, 'output_tokens': 100}
        }
        
        response = client.post('/api/claude/newsletter', json={
            'topic': 'Python',
            'search_count': 5
        })
        
        assert response.status_code == 200
        mock_generate.assert_called_once_with(
            topic='Python',
            style='professional',
            max_tokens=2000,
            search_count=5
        )
    
    @patch('app.claude_service.generate_newsletter_content_claude')
    def test_claude_newsletter_without_search(self, mock_generate, client):
        """Test newsletter generation without search (backwards compatibility)."""
        mock_generate.return_value = {
            'subject': 'Newsletter',
            'content': 'Content with placeholder URLs...',
            'model': 'claude-haiku-4-5',
            'usage': {'input_tokens': 20, 'output_tokens': 100}
        }
        
        response = client.post('/api/claude/newsletter', json={
            'topic': 'Python',
            'use_search': False
        })
        
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        # When use_search is False, articles should not be in response
        assert 'articles' not in data['data']
        mock_generate.assert_called_once_with(
            topic='Python',
            style='professional',
            max_tokens=2000
        )
    
    @patch('app.claude_service.generate_newsletter_content_claude')
    def test_claude_newsletter_success(self, mock_generate, client):
        """Test successful newsletter generation via API (legacy test for backwards compatibility)."""
        mock_generate.return_value = {
            'subject': 'Weekly AI Newsletter',
            'content': 'This week in AI...',
            'model': 'claude-haiku-4-5',
            'usage': {'input_tokens': 30, 'output_tokens': 200}
        }
        
        # Test with use_search=False to use old endpoint
        response = client.post('/api/claude/newsletter', json={
            'topic': 'AI trends',
            'use_search': False
        })
        
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert data['data']['subject'] == 'Weekly AI Newsletter'
        assert data['data']['content'] == 'This week in AI...'
        assert data['data']['model'] == 'claude-haiku-4-5'
        assert 'usage' in data['data']
        mock_generate.assert_called_once()
    
    @patch('app.claude_service.generate_newsletter_content_claude')
    def test_claude_newsletter_with_style(self, mock_generate, client):
        """Test newsletter generation with custom style (legacy)."""
        mock_generate.return_value = {
            'subject': 'Technical Brief',
            'content': 'Technical content...',
            'model': 'claude-haiku-4-5',
            'usage': {'input_tokens': 25, 'output_tokens': 150}
        }
        
        response = client.post('/api/claude/newsletter', json={
            'topic': 'Machine Learning',
            'style': 'technical',
            'use_search': False
        })
        
        assert response.status_code == 200
        mock_generate.assert_called_once_with(
            topic='Machine Learning',
            style='technical',
            max_tokens=2000
        )
    
    @patch('app.claude_service.generate_newsletter_content_claude')
    def test_claude_newsletter_with_max_tokens(self, mock_generate, client):
        """Test newsletter generation with custom max_tokens (legacy)."""
        mock_generate.return_value = {
            'subject': 'Newsletter',
            'content': 'Content...',
            'model': 'claude-haiku-4-5',
            'usage': {'input_tokens': 20, 'output_tokens': 100}
        }
        
        response = client.post('/api/claude/newsletter', json={
            'topic': 'Python',
            'max_tokens': 1500,
            'use_search': False
        })
        
        assert response.status_code == 200
        mock_generate.assert_called_once_with(
            topic='Python',
            style='professional',
            max_tokens=1500
        )
    
    def test_claude_newsletter_missing_data(self, client):
        """Test endpoint with no JSON data."""
        response = client.post('/api/claude/newsletter')
        # Flask returns 415 when no content-type is provided
        assert response.status_code in [400, 415]
    
    def test_claude_newsletter_missing_topic(self, client):
        """Test endpoint with missing topic."""
        response = client.post('/api/claude/newsletter', json={
            'style': 'professional'
        })
        assert response.status_code == 400
        assert 'error' in response.json
        assert 'topic' in response.json['error'].lower()
    
    def test_claude_newsletter_empty_topic(self, client):
        """Test endpoint with empty topic."""
        response = client.post('/api/claude/newsletter', json={
            'topic': ''
        })
        assert response.status_code == 400
        assert 'error' in response.json
    
    @patch('app.claude_service.generate_newsletter_with_search')
    def test_claude_newsletter_api_failure(self, mock_generate, client):
        """Test handling of API failures."""
        mock_generate.return_value = None
        
        response = client.post('/api/claude/newsletter', json={
            'topic': 'Test topic'
        })
        
        assert response.status_code == 500
        assert 'error' in response.json
        assert 'error' in response.json
    
    @patch('app.claude_service.generate_newsletter_with_search')
    def test_claude_newsletter_default_parameters(self, mock_generate, client):
        """Test that default parameters are used when not provided."""
        mock_generate.return_value = {
            'subject': 'Test Subject',
            'content': 'Test Content',
            'articles': [],
            'search_source': 'brave',
            'total_articles': 0,
            'model': 'claude-haiku-4-5',
            'usage': {'input_tokens': 15, 'output_tokens': 80}
        }
        
        response = client.post('/api/claude/newsletter', json={
            'topic': 'Test Topic'
        })
        
        assert response.status_code == 200
        # Verify defaults were used
        call_kwargs = mock_generate.call_args[1]
        assert call_kwargs['style'] == 'professional'
        assert call_kwargs['max_tokens'] == 2000
        assert call_kwargs['search_count'] == 10


class TestClaudeEndpointsIntegration:
    """Integration tests for Claude API endpoints."""

    def test_newsletter_endpoint_exists(self, client):
        """Test that the newsletter endpoint exists and responds."""
        response = client.post('/api/claude/newsletter')
        assert response.status_code in [400, 415, 500]  # Not 404
