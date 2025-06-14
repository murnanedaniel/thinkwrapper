import unittest
import sys
import os
import hashlib
import hmac
import time

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User
import app.services as services # Import services module
from unittest.mock import patch

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test_secret_key',
            'WTF_CSRF_ENABLED': False # Disable CSRF for testing forms if any (not used here but good practice)
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            # Create a test user for login/logout tests
            self.test_user_email = 'test@example.com'
            self.test_user_password = 'password123'
            user = User(email=self.test_user_email)
            user.set_password(self.test_user_password)
            db.session.add(user)
            db.session.commit()
            self.test_user_id = user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_password_hashing(self):
        """Test password hashing and checking."""
        user = User(email='hash@example.com')
        user.set_password('cat')
        self.assertIsNotNone(user.password_hash)
        self.assertNotEqual(user.password_hash, 'cat')
        self.assertTrue(user.check_password('cat'))
        self.assertFalse(user.check_password('dog'))

    def test_register_user_success(self):
        """Test successful user registration."""
        response = self.client.post('/auth/register', json={
            'email': 'newuser@example.com',
            'password': 'newpassword'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['status'], 'success')
        self.assertEqual(response.json['user']['email'], 'newuser@example.com')
        with self.app.app_context():
            user = User.query.filter_by(email='newuser@example.com').first()
            self.assertIsNotNone(user)
            self.assertTrue(user.check_password('newpassword'))

    def test_register_user_missing_fields(self):
        """Test registration with missing email or password."""
        response = self.client.post('/auth/register', json={'email': 'onlyemail@example.com'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

        response = self.client.post('/auth/register', json={'password': 'onlypassword'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_register_user_existing_email(self):
        """Test registration with an already existing email."""
        response = self.client.post('/auth/register', json={
            'email': self.test_user_email, # Existing user
            'password': 'anotherpassword'
        })
        self.assertEqual(response.status_code, 409)
        self.assertIn('error', response.json)

    def test_login_user_success(self):
        """Test successful user login."""
        response = self.client.post('/auth/login', json={
            'email': self.test_user_email,
            'password': self.test_user_password
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'success')
        self.assertEqual(response.json['user']['email'], self.test_user_email)

    def test_login_user_invalid_credentials(self):
        """Test login with invalid email or password."""
        response = self.client.post('/auth/login', json={
            'email': self.test_user_email,
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json)

        response = self.client.post('/auth/login', json={
            'email': 'nouser@example.com',
            'password': 'anypassword'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json)

    def test_logout_user(self):
        """Test user logout."""
        # First, login the user
        self.client.post('/auth/login', json={
            'email': self.test_user_email,
            'password': self.test_user_password
        })
        # Then, logout
        response = self.client.post('/auth/logout')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'success')
        # Verify user is logged out by trying to access a protected route (status)
        status_response = self.client.get('/auth/status')
        self.assertEqual(status_response.status_code, 401) # Unauthorized

    def test_status_endpoint_logged_in(self):
        """Test /auth/status when logged in."""
        self.client.post('/auth/login', json={
            'email': self.test_user_email,
            'password': self.test_user_password
        })
        response = self.client.get('/auth/status')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['user']['id'], self.test_user_id)

    def test_status_endpoint_logged_out(self):
        """Test /auth/status when logged out."""
        response = self.client.get('/auth/status')
        self.assertEqual(response.status_code, 401) # Unauthorized

    # Tests for Paddle Webhook Signature Verification (in services.py)
    def test_verify_paddle_webhook_success(self):
        secret = "test_webhook_secret"
        timestamp = str(int(time.time()))
        payload_body = b'{"event_type":"test.event","data":{"foo":"bar"}}'
        signed_payload_str = f"{timestamp}.{payload_body.decode('utf-8')}"
        expected_hash = hmac.new(secret.encode('utf-8'), signed_payload_str.encode('utf-8'), hashlib.sha256).hexdigest()
        signature_header = f"ts={timestamp};h1={expected_hash}"
        with self.app.app_context():
            with patch.dict(os.environ, {'PADDLE_WEBHOOK_SECRET': secret}):
                is_valid = services.verify_paddle_webhook(payload_body, signature_header)
        self.assertTrue(is_valid)

    def test_verify_paddle_webhook_failure_bad_hash(self):
        secret = "test_webhook_secret"
        timestamp = str(int(time.time()))
        payload_body = b'{"event_type":"test.event","data":{"foo":"bar"}}'
        signature_header = f"ts={timestamp};h1=tamperedhash123"
        with self.app.app_context():
            with patch.dict(os.environ, {'PADDLE_WEBHOOK_SECRET': secret}):
                is_valid = services.verify_paddle_webhook(payload_body, signature_header)
        self.assertFalse(is_valid)

    def test_verify_paddle_webhook_failure_bad_ts(self):
        secret = "test_webhook_secret"
        timestamp = str(int(time.time()))
        tampered_timestamp = str(int(time.time()) - 100)
        payload_body = b'{"event_type":"test.event","data":{"foo":"bar"}}'
        signed_payload_str = f"{tampered_timestamp}.{payload_body.decode('utf-8')}"
        expected_hash = hmac.new(secret.encode('utf-8'), signed_payload_str.encode('utf-8'), hashlib.sha256).hexdigest()
        signature_header = f"ts={timestamp};h1={expected_hash}"
        with self.app.app_context():
            with patch.dict(os.environ, {'PADDLE_WEBHOOK_SECRET': secret}):
                is_valid = services.verify_paddle_webhook(payload_body, signature_header)
        self.assertFalse(is_valid)

    def test_verify_paddle_webhook_no_secret(self):
        timestamp = str(int(time.time()))
        payload_body = b'{"event_type":"test.event"}'
        signature_header = f"ts={timestamp};h1=somehash"
        with self.app.app_context():
            with patch.dict(os.environ, {}, clear=True):
                 if 'PADDLE_WEBHOOK_SECRET' in os.environ: del os.environ['PADDLE_WEBHOOK_SECRET']
                 is_valid = services.verify_paddle_webhook(payload_body, signature_header)
        self.assertFalse(is_valid)

    # Tests for the /auth/paddle/webhook route
    @patch('app.auth.verify_paddle_webhook') # Patch the verification service used in the route
    def test_paddle_webhook_route_success(self, mock_verify_webhook):
        """Test successful processing of a (mocked valid) Paddle webhook."""
        mock_verify_webhook.return_value = True
        user_email = "subscriber@example.com"
        sub_id = "sub_12345"
        with self.app.app_context(): # Ensure user exists for update
            user = User(email=user_email)
            db.session.add(user)
            db.session.commit()

        payload = {
            'event_type': 'subscription.updated',
            'data': {
                'id': sub_id,
                'status': 'active',
                'customer': {'email': user_email}
            }
        }
        response = self.client.post('/auth/paddle/webhook', json=payload, headers={'Paddle-Signature': 'ts=mock;h1=mock'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'webhook processed')
        mock_verify_webhook.assert_called_once()
        with self.app.app_context():
            updated_user = User.query.filter_by(email=user_email).first()
            self.assertTrue(updated_user.is_active)
            self.assertEqual(updated_user.subscription_id, sub_id)

    @patch('app.auth.verify_paddle_webhook')
    def test_paddle_webhook_route_signature_failure(self, mock_verify_webhook):
        """Test Paddle webhook route with signature verification failure."""
        mock_verify_webhook.return_value = False
        payload = {'event_type': 'subscription.created', 'data': {}}
        response = self.client.post('/auth/paddle/webhook', json=payload, headers={'Paddle-Signature': 'ts=invalid;h1=invalid'})
        self.assertEqual(response.status_code, 403)
        self.assertIn('error', response.json)
        mock_verify_webhook.assert_called_once()

    def test_paddle_webhook_route_missing_payload_fields(self):
        """Test Paddle webhook route with missing fields in event payload."""
        # This test will call the real verify_paddle_webhook, so we need a valid sig for it to pass verification stage
        secret = "temp_secret_for_payload_test"
        timestamp = str(int(time.time()))
        payload_body_dict = {
            'event_type': 'subscription.updated', 
            'data': { 'id': 'sub_only_id' } # Missing status and customer email
        }
        payload_body_bytes = str(payload_body_dict).replace("'", '"').encode('utf-8') # crude json bytes
        
        signed_payload_str = f"{timestamp}.{payload_body_bytes.decode('utf-8')}"
        expected_hash = hmac.new(secret.encode('utf-8'), signed_payload_str.encode('utf-8'), hashlib.sha256).hexdigest()
        signature_header = f"ts={timestamp};h1={expected_hash}"

        with patch.dict(os.environ, {'PADDLE_WEBHOOK_SECRET': secret}):
            response = self.client.post('/auth/paddle/webhook', 
                                        data=payload_body_bytes, # Send as raw data due to manual sig
                                        headers={'Paddle-Signature': signature_header, 'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Webhook payload for subscription event missing fields', response.json['error'])

if __name__ == '__main__':
    unittest.main() 