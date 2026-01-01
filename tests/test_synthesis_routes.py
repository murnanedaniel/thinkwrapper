"""
Tests for newsletter synthesis API routes.
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


class TestNewsletterSynthesisRoutes:
    """Test newsletter synthesis admin routes."""
    
    @patch('app.routes.NewsletterSynthesizer')
    @patch('app.routes.NewsletterRenderer')
    def test_synthesize_newsletter_success(self, mock_renderer_class, mock_synthesizer_class, client):
        """Test successful newsletter synthesis."""
        # Mock synthesizer
        mock_synthesizer = Mock()
        mock_synthesizer.generate_on_demand.return_value = {
            'success': True,
            'subject': 'Test Newsletter',
            'content': 'Test content here.',
            'content_items_count': 5,
            'generated_at': '2024-01-01T00:00:00',
            'style': 'professional'
        }
        mock_synthesizer_class.return_value = mock_synthesizer
        
        # Mock renderer
        mock_renderer = Mock()
        mock_renderer.render_html.return_value = '<html>Test HTML</html>'
        mock_renderer_class.return_value = mock_renderer
        
        response = client.post('/api/admin/synthesize', json={
            'newsletter_id': 1,
            'topic': 'AI Weekly',
            'style': 'professional',
            'format': 'html'
        })
        
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert data['subject'] == 'Test Newsletter'
        assert 'rendered' in data
        assert 'html' in data['rendered']
    
    def test_synthesize_newsletter_missing_newsletter_id(self, client):
        """Test synthesis without newsletter_id."""
        response = client.post('/api/admin/synthesize', json={
            'topic': 'Test Topic'
        })
        
        assert response.status_code == 400
        assert 'newsletter_id' in response.json['error']
    
    def test_synthesize_newsletter_missing_topic(self, client):
        """Test synthesis without topic."""
        response = client.post('/api/admin/synthesize', json={
            'newsletter_id': 1
        })
        
        assert response.status_code == 400
        assert 'topic' in response.json['error']
    
    def test_synthesize_newsletter_no_data(self, client):
        """Test synthesis with no data."""
        response = client.post('/api/admin/synthesize', 
                              data='',
                              content_type='application/json')
        
        assert response.status_code == 400
    
    @patch('app.routes.NewsletterSynthesizer')
    @patch('app.routes.NewsletterRenderer')
    def test_synthesize_newsletter_both_formats(self, mock_renderer_class, mock_synthesizer_class, client):
        """Test synthesis with both HTML and text formats."""
        mock_synthesizer = Mock()
        mock_synthesizer.generate_on_demand.return_value = {
            'success': True,
            'subject': 'Test Newsletter',
            'content': 'Test content',
            'content_items_count': 3,
            'generated_at': '2024-01-01T00:00:00',
            'style': 'professional'
        }
        mock_synthesizer_class.return_value = mock_synthesizer
        
        mock_renderer = Mock()
        mock_renderer.render_html.return_value = '<html>HTML</html>'
        mock_renderer.render_plain_text.return_value = 'Plain text'
        mock_renderer_class.return_value = mock_renderer
        
        response = client.post('/api/admin/synthesize', json={
            'newsletter_id': 1,
            'topic': 'Test',
            'format': 'both'
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'html' in data['rendered']
        assert 'text' in data['rendered']
    
    @patch('app.routes.NewsletterSynthesizer')
    @patch('app.routes.NewsletterRenderer')
    def test_synthesize_newsletter_text_format(self, mock_renderer_class, mock_synthesizer_class, client):
        """Test synthesis with text format only."""
        mock_synthesizer = Mock()
        mock_synthesizer.generate_on_demand.return_value = {
            'success': True,
            'subject': 'Test',
            'content': 'Content',
            'content_items_count': 2,
            'generated_at': '2024-01-01T00:00:00',
            'style': 'professional'
        }
        mock_synthesizer_class.return_value = mock_synthesizer
        
        mock_renderer = Mock()
        mock_renderer.render_plain_text.return_value = 'Plain text output'
        mock_renderer_class.return_value = mock_renderer
        
        response = client.post('/api/admin/synthesize', json={
            'newsletter_id': 1,
            'topic': 'Test',
            'format': 'text'
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'text' in data['rendered']
        assert 'html' not in data['rendered']
    
    @patch('app.routes.NewsletterSynthesizer')
    def test_synthesize_newsletter_synthesis_failure(self, mock_synthesizer_class, client):
        """Test handling of synthesis failure."""
        mock_synthesizer = Mock()
        mock_synthesizer.generate_on_demand.return_value = {
            'success': False,
            'error': 'Synthesis failed'
        }
        mock_synthesizer_class.return_value = mock_synthesizer
        
        response = client.post('/api/admin/synthesize', json={
            'newsletter_id': 1,
            'topic': 'Test'
        })
        
        assert response.status_code == 500
        assert 'error' in response.json
    
    @patch('app.routes.NewsletterSynthesizer')
    @patch('app.routes.NewsletterRenderer')
    @patch('app.routes.send_email')
    def test_synthesize_newsletter_with_email(
        self, 
        mock_send_email,
        mock_renderer_class, 
        mock_synthesizer_class, 
        client
    ):
        """Test synthesis with email sending."""
        mock_synthesizer = Mock()
        mock_synthesizer.generate_on_demand.return_value = {
            'success': True,
            'subject': 'Email Newsletter',
            'content': 'Content',
            'content_items_count': 1,
            'generated_at': '2024-01-01T00:00:00',
            'style': 'professional'
        }
        mock_synthesizer_class.return_value = mock_synthesizer
        
        mock_renderer = Mock()
        mock_renderer.render_html.return_value = '<html>Content</html>'
        mock_renderer_class.return_value = mock_renderer
        
        mock_send_email.return_value = True
        
        response = client.post('/api/admin/synthesize', json={
            'newsletter_id': 1,
            'topic': 'Test',
            'send_email': True,
            'email_to': 'test@example.com'
        })
        
        assert response.status_code == 200
        data = response.json
        assert data['metadata']['email_sent'] is True
        mock_send_email.assert_called_once()
    
    def test_synthesize_newsletter_email_without_recipient(self, client):
        """Test synthesis with send_email but no email_to."""
        response = client.post('/api/admin/synthesize', json={
            'newsletter_id': 1,
            'topic': 'Test',
            'send_email': True
        })
        
        assert response.status_code == 400
        assert 'email_to' in response.json['error']


class TestNewsletterConfigRoutes:
    """Test newsletter configuration routes."""
    
    def test_get_newsletter_config(self, client):
        """Test getting newsletter configuration."""
        response = client.get('/api/admin/newsletter/config')
        
        assert response.status_code == 200
        data = response.json
        assert 'schedule' in data
        assert 'delivery_format' in data
        assert 'style' in data
    
    def test_update_newsletter_config_success(self, client):
        """Test updating newsletter configuration."""
        response = client.post('/api/admin/newsletter/config', json={
            'schedule': 'daily',
            'delivery_format': 'text',
            'style': 'casual'
        })
        
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert data['config']['schedule'] == 'daily'
        assert data['config']['style'] == 'casual'
    
    def test_update_newsletter_config_invalid(self, client):
        """Test updating with invalid configuration."""
        response = client.post('/api/admin/newsletter/config', json={
            'schedule': 'invalid_schedule'
        })
        
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_update_newsletter_config_no_data(self, client):
        """Test updating with no data."""
        response = client.post('/api/admin/newsletter/config',
                              data='',
                              content_type='application/json')
        
        assert response.status_code == 400


class TestNewsletterPreviewRoutes:
    """Test newsletter preview routes."""
    
    @patch('app.routes.NewsletterRenderer')
    def test_preview_newsletter_html(self, mock_renderer_class, client):
        """Test previewing newsletter in HTML format."""
        mock_renderer = Mock()
        mock_renderer.render_html.return_value = '<html>Preview</html>'
        mock_renderer_class.return_value = mock_renderer
        
        response = client.post('/api/admin/newsletter/preview', json={
            'subject': 'Test Subject',
            'content': 'Test content',
            'format': 'html'
        })
        
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert 'html' in data['rendered']
    
    @patch('app.routes.NewsletterRenderer')
    def test_preview_newsletter_text(self, mock_renderer_class, client):
        """Test previewing newsletter in text format."""
        mock_renderer = Mock()
        mock_renderer.render_plain_text.return_value = 'Plain preview'
        mock_renderer_class.return_value = mock_renderer
        
        response = client.post('/api/admin/newsletter/preview', json={
            'subject': 'Test Subject',
            'content': 'Test content',
            'format': 'text'
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'text' in data['rendered']
        assert 'html' not in data['rendered']
    
    @patch('app.routes.NewsletterRenderer')
    def test_preview_newsletter_both_formats(self, mock_renderer_class, client):
        """Test previewing newsletter in both formats."""
        mock_renderer = Mock()
        mock_renderer.render_html.return_value = '<html>HTML</html>'
        mock_renderer.render_plain_text.return_value = 'Plain text'
        mock_renderer_class.return_value = mock_renderer
        
        response = client.post('/api/admin/newsletter/preview', json={
            'subject': 'Test Subject',
            'content': 'Test content',
            'format': 'both'
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'html' in data['rendered']
        assert 'text' in data['rendered']
    
    def test_preview_newsletter_missing_subject(self, client):
        """Test preview without subject."""
        response = client.post('/api/admin/newsletter/preview', json={
            'content': 'Test content'
        })
        
        assert response.status_code == 400
        assert 'subject' in response.json['error']
    
    def test_preview_newsletter_missing_content(self, client):
        """Test preview without content."""
        response = client.post('/api/admin/newsletter/preview', json={
            'subject': 'Test Subject'
        })
        
        assert response.status_code == 400
        assert 'content' in response.json['error']
    
    def test_preview_newsletter_no_data(self, client):
        """Test preview with no data."""
        response = client.post('/api/admin/newsletter/preview',
                              data='',
                              content_type='application/json')
        
        assert response.status_code == 400
