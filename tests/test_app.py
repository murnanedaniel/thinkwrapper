import unittest
import sys
import os
from unittest.mock import patch, MagicMock # Import patch and MagicMock
import app.services as services # Import the services module

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User, Newsletter, Issue # Import necessary models and Issue

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'OPENAI_API_KEY': 'test_api_key_for_app_config' # Ensure app has a dummy key for its own checks if any
        })
        self.client = self.app.test_client()
        
        # Create all tables
        with self.app.app_context():
            db.create_all()
            
    def tearDown(self):
        # Drop all tables after each test
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})
        
    @patch('app.routes.generate_newsletter_content')
    @patch('app.routes.send_email') # Add patch for send_email
    def test_generate_newsletter_api_success_contract(self, mock_send_email, mock_generate_service):
        """Test the basic API contract for successful newsletter generation (mocked services)."""
        mock_generate_service.return_value = {
            'subject': 'Mocked Subject for API Test',
            'content': 'Mocked Body for API Test'
        }
        mock_send_email.return_value = True # Assume email sends successfully for this contract test
        payload = {
            'topic': 'Artificial Intelligence',
            'name': 'AI Weekly',
            'schedule': 'weekly'
        }
        response = self.client.post('/api/generate', json=payload)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['status'], 'success')
        self.assertIn('issue_id', response.json)
        self.assertEqual(response.json['subject'], 'Mocked Subject for API Test')
        self.assertEqual(response.json['email_status'], 'sent')
        mock_generate_service.assert_called_once_with('Artificial Intelligence')
        # We expect send_email to be called since a dummy user with an email is created by default
        mock_send_email.assert_called_once()
        # Can add more specific assertions about mock_send_email arguments if needed

    def test_generate_newsletter_api_missing_topic(self):
        """Test the newsletter generation API endpoint with missing topic."""
        response = self.client.post('/api/generate', json={
            'name': 'AI Weekly',
            'schedule': 'weekly'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)
        self.assertEqual(response.json['error'], 'Missing topic or newsletter name')

    def test_create_user(self):
        """Test creating a user."""
        with self.app.app_context():
            user = User(email='test@example.com')
            db.session.add(user)
            db.session.commit()
            
            retrieved_user = User.query.filter_by(email='test@example.com').first()
            self.assertIsNotNone(retrieved_user)
            self.assertEqual(retrieved_user.email, 'test@example.com')

    def test_create_newsletter_model(self): # Renamed for clarity
        """Test creating a newsletter linked to a user."""
        with self.app.app_context():
            user = User(email='user@example.com')
            db.session.add(user)
            db.session.commit()

            newsletter = Newsletter(
                name='Test News',
                topic='Testing',
                user_id=user.id
            )
            db.session.add(newsletter)
            db.session.commit()

            retrieved_newsletter = Newsletter.query.filter_by(name='Test News').first()
            self.assertIsNotNone(retrieved_newsletter)
            self.assertEqual(retrieved_newsletter.topic, 'Testing')
            self.assertEqual(retrieved_newsletter.user_id, user.id)
            self.assertEqual(retrieved_newsletter.user.email, 'user@example.com')
        
    @patch('app.services.client.chat.completions.create')
    def test_generate_newsletter_content_service_success(self, mock_openai_call):
        """Test the generate_newsletter_content service on success."""
        mock_openai_call.return_value.choices = [
            type('Choice', (object,), {
                'message': type('Message', (object,), {
                    'content': 'Test Subject\nTest Body Content'
                })
            })
        ]
        
        with self.app.app_context(): # Need app context for current_app.logger and API key check
            # Mock the API key for the service call if it's checked inside
            with patch.object(services.client, 'api_key', 'test_key'): 
                result = services.generate_newsletter_content('Test Topic')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['subject'], 'Test Subject')
        self.assertEqual(result['content'], 'Test Body Content')
        mock_openai_call.assert_called_once()

    @patch('app.services.client.chat.completions.create')
    def test_generate_newsletter_content_service_failure(self, mock_openai_call):
        """Test the generate_newsletter_content service on OpenAI API failure."""
        mock_openai_call.side_effect = Exception("OpenAI API Error")
        
        with self.app.app_context():
            with patch.object(services.client, 'api_key', 'test_key'):
                 result = services.generate_newsletter_content('Test Topic')
            
        self.assertIsNone(result)
        mock_openai_call.assert_called_once()

    @patch('app.routes.generate_newsletter_content')
    @patch('app.routes.send_email') # Add patch for send_email
    def test_generate_newsletter_route_success_saves_db_sends_email(self, mock_send_email, mock_generate_service):
        """Test /api/generate: success, saves to DB, and calls send_email."""
        mock_generate_service.return_value = {
            'subject': 'Generated Subject DB Email',
            'content': 'Generated Body DB Email'
        }
        mock_send_email.return_value = True # Simulate successful email send

        payload = {
            'topic': 'Quantum Computing DB Email',
            'name': 'Quantum News DB Email',
            'schedule': 'monthly'
        }
        response = self.client.post('/api/generate', json=payload)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['status'], 'success')
        self.assertEqual(response.json['subject'], 'Generated Subject DB Email')
        self.assertEqual(response.json['email_status'], 'sent')
        mock_generate_service.assert_called_once_with('Quantum Computing DB Email')
        
        with self.app.app_context():
            user = User.query.filter_by(email='default_user@example.com').first()
            self.assertIsNotNone(user)
            issue = Issue.query.filter_by(subject='Generated Subject DB Email').first()
            self.assertIsNotNone(issue)
            self.assertEqual(issue.content, 'Generated Body DB Email')
            self.assertIsNotNone(issue.sent_at) # Check that sent_at is updated
            newsletter = Newsletter.query.filter_by(name='Quantum News DB Email').first()
            self.assertIsNotNone(newsletter)
            self.assertEqual(issue.newsletter_id, newsletter.id)
            
            mock_send_email.assert_called_once_with(
                to_email_address=user.email,
                subject='Generated Subject DB Email',
                html_content='Generated Body DB Email'
            )

    @patch('app.routes.generate_newsletter_content')
    @patch('app.routes.send_email') # Add patch for send_email
    def test_generate_newsletter_route_email_failure(self, mock_send_email, mock_generate_service):
        """Test /api/generate: success in generation, but email sending fails."""
        mock_generate_service.return_value = {
            'subject': 'Generated Subject Email Fail',
            'content': 'Generated Body Email Fail'
        }
        mock_send_email.return_value = False # Simulate email sending failure

        payload = {
            'topic': 'Topic Email Fail',
            'name': 'News Email Fail',
            'schedule': 'daily'
        }
        response = self.client.post('/api/generate', json=payload)
        
        self.assertEqual(response.status_code, 201) # Still 201 as generation succeeded
        self.assertEqual(response.json['status'], 'success')
        self.assertEqual(response.json['email_status'], 'failed')
        self.assertIn('Email sending failed or skipped', response.json['message'])
        mock_generate_service.assert_called_once_with('Topic Email Fail')
        mock_send_email.assert_called_once() # Still called
        with self.app.app_context():
            issue = Issue.query.filter_by(subject='Generated Subject Email Fail').first()
            self.assertIsNotNone(issue)
            self.assertIsNone(issue.sent_at) # Check that sent_at is NOT updated

    @patch('app.services.sendgrid.SendGridAPIClient') # Patch the SendGrid client
    def test_send_email_service_success(self, mock_sendgrid_client_constructor):
        """Test the send_email service on success."""
        mock_sg_instance = MagicMock()
        # sg.send(message) returns a response object directly, not client.mail.send.post
        mock_sg_instance.send.return_value = MagicMock(status_code=202) 
        mock_sendgrid_client_constructor.return_value = mock_sg_instance

        with self.app.app_context():
            with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_sendgrid_key'}):
                success = services.send_email(
                    to_email_address='recipient@example.com', # Updated arg name
                    subject='Test Email Subject',
                    html_content='<p>Test email content.</p>' # Updated arg name
                )
        
        self.assertTrue(success)
        mock_sendgrid_client_constructor.assert_called_once_with(api_key='test_sendgrid_key')
        mock_sg_instance.send.assert_called_once() # Check that sg.send was called

    @patch('app.services.sendgrid.SendGridAPIClient')
    def test_send_email_service_failure(self, mock_sendgrid_client_constructor):
        """Test the send_email service on SendGrid API failure."""
        mock_sg_instance = MagicMock()
        mock_sg_instance.send.side_effect = Exception("SendGrid API Error") # Mock sg.send
        mock_sendgrid_client_constructor.return_value = mock_sg_instance

        with self.app.app_context():
            with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_sendgrid_key'}):
                success = services.send_email(
                    to_email_address='recipient@example.com', # Updated arg name
                    subject='Test Email Subject',
                    html_content='<p>Test email content.</p>' # Updated arg name
                )
                
        self.assertFalse(success)
        mock_sendgrid_client_constructor.assert_called_once_with(api_key='test_sendgrid_key')

    @patch('app.services.sendgrid.SendGridAPIClient')
    def test_send_email_service_no_api_key(self, mock_sendgrid_client_constructor):
        """Test the send_email service when SENDGRID_API_KEY is not set."""
        with self.app.app_context():
            with patch.dict(os.environ, {}, clear=True):
                if 'SENDGRID_API_KEY' in os.environ: del os.environ['SENDGRID_API_KEY']
                success = services.send_email(
                    to_email_address='recipient@example.com', # Updated arg name
                    subject='Test Email Subject',
                    html_content='<p>Test email content.</p>' # Updated arg name
                )
        self.assertFalse(success)
        mock_sendgrid_client_constructor.assert_not_called()

if __name__ == '__main__':
    unittest.main() 