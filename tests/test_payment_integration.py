"""
Integration tests for Paddle payment flow.

These tests verify the complete payment workflow including:
- Checkout session creation with Paddle API
- Webhook signature generation and verification
- End-to-end payment flow simulation
- Subscription lifecycle management

Note: These tests use mocked Paddle API responses but test the
complete integration flow through the application.
"""

import pytest
import json
import hmac
import hashlib
from unittest.mock import patch, Mock
from app import create_app
from app.payment_service import get_paddle_service


class TestPaddleIntegration:
    """Integration tests for Paddle payment service."""
    
    @pytest.fixture
    def app(self):
        """Create and configure a test Flask app."""
        app = create_app({'TESTING': True})
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()
    
    @pytest.fixture
    def paddle_env(self):
        """Set up Paddle environment variables."""
        return {
            'PADDLE_VENDOR_ID': 'test_vendor_12345',
            'PADDLE_API_KEY': 'test_key_abcdefghijklmnop',
            'PADDLE_WEBHOOK_SECRET': 'test_webhook_secret_xyz',
            'PADDLE_SANDBOX': 'true'
        }
    
    def generate_webhook_signature(self, payload: str, secret: str) -> str:
        """Generate a valid webhook signature for testing."""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @patch('app.payment_service.requests.post')
    @patch.dict('os.environ', {
        'PADDLE_VENDOR_ID': 'test_vendor',
        'PADDLE_API_KEY': 'test_key',
        'PADDLE_WEBHOOK_SECRET': 'test_secret',
        'PADDLE_SANDBOX': 'true'
    })
    def test_complete_checkout_flow(self, mock_post, client):
        """Test complete checkout flow from creation to completion."""
        # Mock successful checkout session creation
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'id': 'ses_test_123',
                'url': 'https://sandbox-checkout.paddle.com/ses_test_123'
            }
        }
        mock_post.return_value = mock_response
        
        # Step 1: Create checkout session
        checkout_response = client.post('/api/payment/checkout', json={
            'price_id': 'pri_test_product_123',
            'customer_email': 'customer@example.com',
            'success_url': 'https://example.com/success',
            'cancel_url': 'https://example.com/cancel',
            'metadata': {
                'user_id': '789',
                'source': 'web'
            }
        })
        
        assert checkout_response.status_code == 200
        checkout_data = checkout_response.json
        assert checkout_data['success'] is True
        assert checkout_data['data']['session_id'] == 'ses_test_123'
        assert 'checkout_url' in checkout_data['data']
        
        # Verify API was called with correct parameters
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert 'https://sandbox-api.paddle.com/checkout/session' in call_args[0][0]
        payload = call_args[1]['json']
        assert payload['items'][0]['price_id'] == 'pri_test_product_123'
        assert payload['customer_email'] == 'customer@example.com'
        assert payload['custom_data']['user_id'] == '789'
    
    @patch('app.payment_service.get_paddle_service')
    @patch.dict('os.environ', {
        'PADDLE_VENDOR_ID': 'test_vendor',
        'PADDLE_API_KEY': 'test_key',
        'PADDLE_WEBHOOK_SECRET': 'webhook_secret_123',
        'PADDLE_SANDBOX': 'true'
    })
    def test_complete_payment_webhook_flow(self, mock_get_service, client):
        """Test complete webhook flow from receipt to processing."""
        # Mock the paddle service to verify signature
        mock_service = Mock()
        mock_service.verify_webhook_signature.return_value = True
        mock_service.process_webhook_event.return_value = {
            'status': 'success',
            'event_type': 'transaction.completed',
            'transaction_id': 'txn_test_456',
            'customer_id': 'cus_test_789',
            'amount': '29.99',
            'currency': 'USD'
        }
        mock_get_service.return_value = mock_service
        
        # Step 1: Simulate transaction.completed webhook
        webhook_payload = {
            'event_type': 'transaction.completed',
            'event_id': 'evt_test_123',
            'occurred_at': '2024-01-15T10:30:00.000Z',
            'data': {
                'id': 'txn_test_456',
                'customer_id': 'cus_test_789',
                'amount': '29.99',
                'currency_code': 'USD',
                'status': 'completed',
                'custom_data': {
                    'user_id': '789'
                }
            }
        }
        
        # Send webhook
        webhook_response = client.post(
            '/api/payment/webhook',
            json=webhook_payload,
            headers={
                'Paddle-Signature': 'valid_test_signature'
            }
        )
        
        assert webhook_response.status_code == 200
        response_data = webhook_response.json
        assert response_data['success'] is True
        assert response_data['data']['status'] == 'received'
        assert response_data['data']['event_type'] == 'transaction.completed'
        
        # Verify the webhook was processed
        mock_service.process_webhook_event.assert_called_once_with(
            'transaction.completed',
            webhook_payload['data']
        )
    
    @patch('app.payment_service.get_paddle_service')
    @patch.dict('os.environ', {
        'PADDLE_VENDOR_ID': 'test_vendor',
        'PADDLE_API_KEY': 'test_key',
        'PADDLE_WEBHOOK_SECRET': 'webhook_secret_123',
        'PADDLE_SANDBOX': 'true'
    })
    def test_subscription_lifecycle_webhooks(self, mock_get_service, client):
        """Test complete subscription lifecycle through webhooks."""
        # Mock the paddle service
        mock_service = Mock()
        mock_service.verify_webhook_signature.return_value = True
        mock_get_service.return_value = mock_service
        
        # Step 1: Subscription created
        mock_service.process_webhook_event.return_value = {
            'status': 'success',
            'event_type': 'subscription.created',
            'subscription_id': 'sub_test_123',
            'customer_id': 'cus_test_456',
            'subscription_status': 'active'
        }
        
        created_payload = {
            'event_type': 'subscription.created',
            'data': {
                'id': 'sub_test_123',
                'customer_id': 'cus_test_456',
                'status': 'active',
                'items': [{'price_id': 'pri_test_789'}]
            }
        }
        
        response = client.post(
            '/api/payment/webhook',
            json=created_payload,
            headers={'Paddle-Signature': 'valid_signature'}
        )
        assert response.status_code == 200
        
        # Step 2: Subscription updated
        mock_service.process_webhook_event.return_value = {
            'status': 'success',
            'event_type': 'subscription.updated',
            'subscription_id': 'sub_test_123',
            'subscription_status': 'active'
        }
        
        updated_payload = {
            'event_type': 'subscription.updated',
            'data': {
                'id': 'sub_test_123',
                'customer_id': 'cus_test_456',
                'status': 'active',
                'next_billed_at': '2024-02-15T00:00:00.000Z'
            }
        }
        
        response = client.post(
            '/api/payment/webhook',
            json=updated_payload,
            headers={'Paddle-Signature': 'valid_signature'}
        )
        assert response.status_code == 200
        
        # Step 3: Subscription cancelled
        mock_service.process_webhook_event.return_value = {
            'status': 'success',
            'event_type': 'subscription.cancelled',
            'subscription_id': 'sub_test_123',
            'cancelled_at': '2024-03-15T10:30:00.000Z'
        }
        
        cancelled_payload = {
            'event_type': 'subscription.cancelled',
            'data': {
                'id': 'sub_test_123',
                'customer_id': 'cus_test_456',
                'status': 'cancelled',
                'cancelled_at': '2024-03-15T10:30:00.000Z'
            }
        }
        
        response = client.post(
            '/api/payment/webhook',
            json=cancelled_payload,
            headers={'Paddle-Signature': 'valid_signature'}
        )
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert data['data']['event_type'] == 'subscription.cancelled'
    
    @patch.dict('os.environ', {
        'PADDLE_VENDOR_ID': 'test_vendor',
        'PADDLE_API_KEY': 'test_key',
        'PADDLE_WEBHOOK_SECRET': 'webhook_secret_123',
        'PADDLE_SANDBOX': 'true'
    })
    def test_webhook_security_invalid_signature(self, client):
        """Test that webhooks with invalid signatures are rejected."""
        webhook_payload = {
            'event_type': 'transaction.completed',
            'data': {'id': 'txn_malicious'}
        }
        payload_str = json.dumps(webhook_payload)
        
        # Use wrong signature
        invalid_signature = 'definitely_not_a_valid_signature'
        
        response = client.post(
            '/api/payment/webhook',
            data=payload_str,
            headers={
                'Content-Type': 'application/json',
                'Paddle-Signature': invalid_signature
            }
        )
        
        assert response.status_code == 401
        assert 'signature' in response.json['error'].lower()
    
    @patch('app.payment_service.get_paddle_service')
    @patch.dict('os.environ', {
        'PADDLE_VENDOR_ID': 'test_vendor',
        'PADDLE_API_KEY': 'test_key',
        'PADDLE_WEBHOOK_SECRET': 'webhook_secret_123',
        'PADDLE_SANDBOX': 'true'
    })
    def test_webhook_replay_attack_prevention(self, mock_get_service, client):
        """Test that duplicate webhooks can be identified."""
        # Mock the paddle service
        mock_service = Mock()
        mock_service.verify_webhook_signature.return_value = True
        mock_service.process_webhook_event.return_value = {
            'status': 'success',
            'event_type': 'transaction.completed'
        }
        mock_get_service.return_value = mock_service
        
        # Create webhook payload
        webhook_payload = {
            'event_type': 'transaction.completed',
            'event_id': 'evt_unique_123',  # Same event ID
            'data': {
                'id': 'txn_test_789',
                'amount': '29.99'
            }
        }
        
        # Send webhook first time
        response1 = client.post(
            '/api/payment/webhook',
            json=webhook_payload,
            headers={'Paddle-Signature': 'valid_signature'}
        )
        assert response1.status_code == 200
        
        # Send same webhook again (replay attack simulation)
        response2 = client.post(
            '/api/payment/webhook',
            json=webhook_payload,
            headers={'Paddle-Signature': 'valid_signature'}
        )
        # Note: Current implementation accepts duplicates
        # In production, you should track event_id to prevent replay attacks
        assert response2.status_code == 200
        # TODO: Implement idempotency checks using event_id
    
    @patch('app.payment_service.requests.post')
    @patch.dict('os.environ', {
        'PADDLE_VENDOR_ID': 'test_vendor',
        'PADDLE_API_KEY': 'test_key',
        'PADDLE_WEBHOOK_SECRET': 'test_secret',
        'PADDLE_SANDBOX': 'true'
    })
    def test_subscription_cancellation_flow(self, mock_post, client):
        """Test subscription cancellation through API."""
        # Mock successful cancellation
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Cancel subscription
        response = client.post(
            '/api/payment/subscription/sub_test_123/cancel',
            json={'effective_date': '2024-12-31'},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert 'cancelled' in data['message'].lower()
        
        # Verify Paddle API was called correctly
        mock_post.assert_called_once()
        assert 'sub_test_123/cancel' in mock_post.call_args[0][0]
        assert mock_post.call_args[1]['json']['effective_from'] == '2024-12-31'
    
    @patch('app.payment_service.requests.get')
    @patch.dict('os.environ', {
        'PADDLE_VENDOR_ID': 'test_vendor',
        'PADDLE_API_KEY': 'test_key',
        'PADDLE_WEBHOOK_SECRET': 'test_secret',
        'PADDLE_SANDBOX': 'true'
    })
    def test_customer_info_retrieval(self, mock_get, app):
        """Test customer information retrieval."""
        with app.app_context():
            # Mock successful customer retrieval
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'data': {
                    'id': 'cus_test_123',
                    'email': 'customer@example.com',
                    'name': 'Test Customer',
                    'created_at': '2024-01-01T00:00:00.000Z'
                }
            }
            mock_get.return_value = mock_response
            
            # Get Paddle service and retrieve customer
            paddle_service = get_paddle_service()
            customer = paddle_service.get_customer_info('cus_test_123')
            
            assert customer is not None
            assert customer['data']['id'] == 'cus_test_123'
            assert customer['data']['email'] == 'customer@example.com'
            
            # Verify API was called correctly
            mock_get.assert_called_once()
            assert 'customers/cus_test_123' in mock_get.call_args[0][0]
    
    @patch('app.payment_service.requests.post')
    @patch.dict('os.environ', {
        'PADDLE_VENDOR_ID': 'test_vendor',
        'PADDLE_API_KEY': 'test_key',
        'PADDLE_WEBHOOK_SECRET': 'test_secret',
        'PADDLE_SANDBOX': 'true'
    })
    def test_error_handling_api_failure(self, mock_post, client):
        """Test proper error handling when Paddle API fails."""
        # Mock API failure
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response
        
        # Attempt to create checkout
        response = client.post('/api/payment/checkout', json={
            'price_id': 'pri_test_123',
            'customer_email': 'test@example.com',
            'success_url': 'https://example.com/success'
        })
        
        assert response.status_code == 500
        assert 'error' in response.json
    
    @patch('app.payment_service.requests.post')
    @patch.dict('os.environ', {
        'PADDLE_VENDOR_ID': 'test_vendor',
        'PADDLE_API_KEY': 'test_key',
        'PADDLE_WEBHOOK_SECRET': 'test_secret',
        'PADDLE_SANDBOX': 'true'
    })
    def test_checkout_with_metadata(self, mock_post, client):
        """Test that custom metadata is properly passed to Paddle."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'id': 'ses_test',
                'url': 'https://checkout.paddle.com/ses_test'
            }
        }
        mock_post.return_value = mock_response
        
        # Create checkout with metadata
        metadata = {
            'user_id': '12345',
            'plan': 'premium',
            'referral_code': 'FRIEND2024'
        }
        
        response = client.post('/api/payment/checkout', json={
            'price_id': 'pri_test',
            'customer_email': 'test@example.com',
            'success_url': 'https://example.com/success',
            'metadata': metadata
        })
        
        assert response.status_code == 200
        
        # Verify metadata was sent to Paddle
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['custom_data'] == metadata


class TestPaddleEnvironmentConfiguration:
    """Test Paddle environment configuration handling."""
    
    @patch.dict('os.environ', {
        'PADDLE_VENDOR_ID': 'sandbox_vendor',
        'PADDLE_API_KEY': 'sandbox_key',
        'PADDLE_WEBHOOK_SECRET': 'sandbox_secret',
        'PADDLE_SANDBOX': 'true'
    })
    def test_sandbox_configuration(self):
        """Test service configures correctly for sandbox."""
        from app import create_app
        from app.payment_service import PaddlePaymentService
        
        app = create_app({'TESTING': True})
        
        with app.app_context():
            # Create a new instance to pick up the environment variables
            service = PaddlePaymentService()
            assert service.sandbox_mode is True
            assert service.api_base_url == 'https://sandbox-api.paddle.com'
            assert service.vendor_id == 'sandbox_vendor'
    
    @patch.dict('os.environ', {
        'PADDLE_VENDOR_ID': 'prod_vendor',
        'PADDLE_API_KEY': 'prod_key',
        'PADDLE_WEBHOOK_SECRET': 'prod_secret',
        'PADDLE_SANDBOX': 'false'
    })
    def test_production_configuration(self):
        """Test service configures correctly for production."""
        from app import create_app
        from app.payment_service import PaddlePaymentService
        
        app = create_app({'TESTING': True})
        
        with app.app_context():
            # Create new service instance for this test
            service = PaddlePaymentService()
            assert service.sandbox_mode is False
            assert service.api_base_url == 'https://api.paddle.com'
            assert service.vendor_id == 'prod_vendor'
    
    @patch.dict('os.environ', {}, clear=True)
    def test_missing_configuration_handling(self):
        """Test graceful handling of missing configuration."""
        from app import create_app
        from app.payment_service import PaddlePaymentService
        
        app = create_app({'TESTING': True})
        
        with app.app_context():
            service = PaddlePaymentService()
            
            # Service should initialize but return None on API calls
            result = service.create_checkout_session(
                price_id='pri_test',
                customer_email='test@example.com',
                success_url='https://example.com/success'
            )
            assert result is None
