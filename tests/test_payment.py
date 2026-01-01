"""
Tests for Paddle payment integration.

This module tests:
- Payment checkout session creation
- Webhook signature verification
- Webhook event processing
- Subscription management
"""

import pytest
import json
import hmac
import hashlib
from unittest.mock import patch, Mock, MagicMock
from app import create_app
from app.payment_service import PaddlePaymentService, get_paddle_service


class TestPaddlePaymentService:
    """Test Paddle payment service functionality."""
    
    @pytest.fixture
    def payment_service(self):
        """Create a payment service instance with test credentials."""
        from app import create_app
        app = create_app({'TESTING': True})
        with app.app_context():
            with patch.dict('os.environ', {
                'PADDLE_VENDOR_ID': 'test_vendor_123',
                'PADDLE_API_KEY': 'test_api_key',
                'PADDLE_WEBHOOK_SECRET': 'test_webhook_secret',
                'PADDLE_SANDBOX': 'true'
            }):
                service = PaddlePaymentService()
                yield service
    
    def test_service_initialization_sandbox(self, payment_service):
        """Test service initializes with sandbox configuration."""
        assert payment_service.vendor_id == 'test_vendor_123'
        assert payment_service.api_key == 'test_api_key'
        assert payment_service.webhook_secret == 'test_webhook_secret'
        assert payment_service.sandbox_mode is True
        assert payment_service.api_base_url == 'https://sandbox-api.paddle.com'
    
    @patch.dict('os.environ', {
        'PADDLE_VENDOR_ID': 'prod_vendor',
        'PADDLE_API_KEY': 'prod_key',
        'PADDLE_WEBHOOK_SECRET': 'prod_secret',
        'PADDLE_SANDBOX': 'false'
    })
    def test_service_initialization_production(self):
        """Test service initializes with production configuration."""
        service = PaddlePaymentService()
        assert service.sandbox_mode is False
        assert service.api_base_url == 'https://api.paddle.com'
    
    @patch('app.payment_service.requests.post')
    def test_create_checkout_session_success(self, mock_post, payment_service):
        """Test successful checkout session creation."""
        # Mock successful Paddle API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'id': 'ses_123',
                'url': 'https://checkout.paddle.com/ses_123'
            }
        }
        mock_post.return_value = mock_response
        
        result = payment_service.create_checkout_session(
            price_id='pri_123',
            customer_email='test@example.com',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
            metadata={'user_id': '456'}
        )
        
        assert result is not None
        assert result['data']['id'] == 'ses_123'
        assert result['data']['url'] == 'https://checkout.paddle.com/ses_123'
        
        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert 'https://sandbox-api.paddle.com/checkout/session' in call_args[0]
        assert call_args[1]['headers']['Authorization'] == 'Bearer test_api_key'
        
        payload = call_args[1]['json']
        assert payload['items'][0]['price_id'] == 'pri_123'
        assert payload['customer_email'] == 'test@example.com'
        assert payload['success_url'] == 'https://example.com/success'
        assert payload['cancel_url'] == 'https://example.com/cancel'
        assert payload['custom_data'] == {'user_id': '456'}
    
    @patch('app.payment_service.requests.post')
    def test_create_checkout_session_without_cancel_url(self, mock_post, payment_service):
        """Test checkout session creation without cancel URL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'id': 'ses_123'}}
        mock_post.return_value = mock_response
        
        result = payment_service.create_checkout_session(
            price_id='pri_123',
            customer_email='test@example.com',
            success_url='https://example.com/success'
        )
        
        assert result is not None
        payload = mock_post.call_args[1]['json']
        assert 'cancel_url' not in payload
    
    @patch('app.payment_service.requests.post')
    def test_create_checkout_session_api_error(self, mock_post, payment_service):
        """Test checkout session creation with API error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Invalid price_id'
        mock_post.return_value = mock_response
        
        result = payment_service.create_checkout_session(
            price_id='invalid',
            customer_email='test@example.com',
            success_url='https://example.com/success'
        )
        
        assert result is None
    
    @patch.dict('os.environ', {}, clear=True)
    def test_create_checkout_session_missing_credentials(self):
        """Test checkout session creation without credentials."""
        from app import create_app
        app = create_app({'TESTING': True})
        with app.app_context():
            service = PaddlePaymentService()
            
            result = service.create_checkout_session(
                price_id='pri_123',
                customer_email='test@example.com',
                success_url='https://example.com/success'
            )
            
            assert result is None
    
    def test_verify_webhook_signature_valid(self, payment_service):
        """Test webhook signature verification with valid signature."""
        payload = json.dumps({'event_type': 'transaction.completed'})
        
        # Generate valid signature
        signature = hmac.new(
            'test_webhook_secret'.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        assert payment_service.verify_webhook_signature(payload, signature) is True
    
    def test_verify_webhook_signature_invalid(self, payment_service):
        """Test webhook signature verification with invalid signature."""
        payload = json.dumps({'event_type': 'transaction.completed'})
        invalid_signature = 'invalid_signature_123'
        
        assert payment_service.verify_webhook_signature(payload, invalid_signature) is False
    
    @patch.dict('os.environ', {}, clear=True)
    def test_verify_webhook_signature_missing_secret(self):
        """Test webhook signature verification without secret."""
        from app import create_app
        app = create_app({'TESTING': True})
        with app.app_context():
            service = PaddlePaymentService()
            result = service.verify_webhook_signature('payload', 'signature')
            assert result is False
    
    def test_process_webhook_event_transaction_completed(self, payment_service):
        """Test processing transaction.completed webhook."""
        event_data = {
            'id': 'txn_123',
            'customer_id': 'cus_456',
            'amount': '29.99',
            'currency_code': 'USD'
        }
        
        result = payment_service.process_webhook_event(
            'transaction.completed',
            event_data
        )
        
        assert result['status'] == 'success'
        assert result['event_type'] == 'transaction.completed'
        assert result['transaction_id'] == 'txn_123'
        assert result['customer_id'] == 'cus_456'
        assert result['amount'] == '29.99'
        assert result['currency'] == 'USD'
    
    def test_process_webhook_event_subscription_created(self, payment_service):
        """Test processing subscription.created webhook."""
        event_data = {
            'id': 'sub_123',
            'customer_id': 'cus_456',
            'status': 'active'
        }
        
        result = payment_service.process_webhook_event(
            'subscription.created',
            event_data
        )
        
        assert result['status'] == 'success'
        assert result['event_type'] == 'subscription.created'
        assert result['subscription_id'] == 'sub_123'
        assert result['customer_id'] == 'cus_456'
        assert result['subscription_status'] == 'active'
    
    def test_process_webhook_event_subscription_cancelled(self, payment_service):
        """Test processing subscription.cancelled webhook."""
        event_data = {
            'id': 'sub_123',
            'cancelled_at': '2024-12-31T23:59:59Z'
        }
        
        result = payment_service.process_webhook_event(
            'subscription.cancelled',
            event_data
        )
        
        assert result['status'] == 'success'
        assert result['event_type'] == 'subscription.cancelled'
        assert result['subscription_id'] == 'sub_123'
        assert result['cancelled_at'] == '2024-12-31T23:59:59Z'
    
    def test_process_webhook_event_unhandled_type(self, payment_service):
        """Test processing unhandled webhook event type."""
        result = payment_service.process_webhook_event(
            'unknown.event',
            {}
        )
        
        assert result['status'] == 'unhandled'
        assert result['event_type'] == 'unknown.event'
    
    @patch('app.payment_service.requests.get')
    def test_get_customer_info_success(self, mock_get, payment_service):
        """Test successful customer info retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'id': 'cus_123',
                'email': 'test@example.com',
                'name': 'Test User'
            }
        }
        mock_get.return_value = mock_response
        
        result = payment_service.get_customer_info('cus_123')
        
        assert result is not None
        assert result['data']['id'] == 'cus_123'
        assert result['data']['email'] == 'test@example.com'
        
        mock_get.assert_called_once()
        assert 'cus_123' in mock_get.call_args[0][0]
    
    @patch('app.payment_service.requests.get')
    def test_get_customer_info_not_found(self, mock_get, payment_service):
        """Test customer info retrieval for non-existent customer."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = payment_service.get_customer_info('cus_invalid')
        
        assert result is None
    
    @patch('app.payment_service.requests.post')
    def test_cancel_subscription_success(self, mock_post, payment_service):
        """Test successful subscription cancellation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = payment_service.cancel_subscription('sub_123')
        
        assert result is True
        mock_post.assert_called_once()
        assert 'sub_123/cancel' in mock_post.call_args[0][0]
    
    @patch('app.payment_service.requests.post')
    def test_cancel_subscription_with_effective_date(self, mock_post, payment_service):
        """Test subscription cancellation with effective date."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        result = payment_service.cancel_subscription(
            'sub_123',
            effective_date='2024-12-31'
        )
        
        assert result is True
        payload = mock_post.call_args[1]['json']
        assert payload['effective_from'] == '2024-12-31'
    
    @patch('app.payment_service.requests.post')
    def test_cancel_subscription_failure(self, mock_post, payment_service):
        """Test failed subscription cancellation."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        result = payment_service.cancel_subscription('sub_123')
        
        assert result is False


class TestPaymentRoutes:
    """Test payment-related API routes."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the app."""
        app = create_app({'TESTING': True})
        with app.test_client() as client:
            yield client
    
    @patch('app.payment_service.get_paddle_service')
    def test_create_payment_checkout_success(self, mock_get_service, client):
        """Test successful checkout session creation endpoint."""
        mock_service = Mock()
        mock_service.create_checkout_session.return_value = {
            'data': {
                'id': 'ses_123',
                'url': 'https://checkout.paddle.com/ses_123'
            }
        }
        mock_get_service.return_value = mock_service
        
        response = client.post('/api/payment/checkout', json={
            'price_id': 'pri_123',
            'customer_email': 'test@example.com',
            'success_url': 'https://example.com/success',
            'cancel_url': 'https://example.com/cancel',
            'metadata': {'user_id': '789'}
        })
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'
        assert data['checkout_url'] == 'https://checkout.paddle.com/ses_123'
        assert data['session_id'] == 'ses_123'
        
        mock_service.create_checkout_session.assert_called_once_with(
            price_id='pri_123',
            customer_email='test@example.com',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
            metadata={'user_id': '789'}
        )
    
    def test_create_payment_checkout_missing_data(self, client):
        """Test checkout endpoint with missing data."""
        response = client.post('/api/payment/checkout', 
                              data='',
                              content_type='application/json')
        # Flask returns 400 for empty body with JSON content type
        assert response.status_code in [400, 415]
    
    def test_create_payment_checkout_missing_fields(self, client):
        """Test checkout endpoint with missing required fields."""
        response = client.post('/api/payment/checkout', json={
            'customer_email': 'test@example.com'
        })
        
        assert response.status_code == 400
        assert 'error' in response.json
        assert 'required fields' in response.json['error'].lower()
    
    @patch('app.payment_service.get_paddle_service')
    def test_create_payment_checkout_service_failure(self, mock_get_service, client):
        """Test checkout endpoint when service fails."""
        mock_service = Mock()
        mock_service.create_checkout_session.return_value = None
        mock_get_service.return_value = mock_service
        
        response = client.post('/api/payment/checkout', json={
            'price_id': 'pri_123',
            'customer_email': 'test@example.com',
            'success_url': 'https://example.com/success'
        })
        
        assert response.status_code == 500
        assert 'error' in response.json
    
    @patch('app.payment_service.get_paddle_service')
    def test_paddle_webhook_success(self, mock_get_service, client):
        """Test successful webhook processing."""
        mock_service = Mock()
        mock_service.verify_webhook_signature.return_value = True
        mock_service.process_webhook_event.return_value = {
            'status': 'success',
            'event_type': 'transaction.completed'
        }
        mock_get_service.return_value = mock_service
        
        response = client.post(
            '/api/payment/webhook',
            json={
                'event_type': 'transaction.completed',
                'data': {'id': 'txn_123'}
            },
            headers={'Paddle-Signature': 'valid_signature'}
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'received'
        assert data['event_type'] == 'transaction.completed'
    
    def test_paddle_webhook_missing_signature(self, client):
        """Test webhook endpoint without signature."""
        response = client.post(
            '/api/payment/webhook',
            json={'event_type': 'test'}
        )
        
        assert response.status_code == 400
        assert 'signature' in response.json['error'].lower()
    
    @patch('app.payment_service.get_paddle_service')
    def test_paddle_webhook_invalid_signature(self, mock_get_service, client):
        """Test webhook endpoint with invalid signature."""
        mock_service = Mock()
        mock_service.verify_webhook_signature.return_value = False
        mock_get_service.return_value = mock_service
        
        response = client.post(
            '/api/payment/webhook',
            json={'event_type': 'test'},
            headers={'Paddle-Signature': 'invalid_signature'}
        )
        
        assert response.status_code == 401
        assert 'signature' in response.json['error'].lower()
    
    @patch('app.payment_service.get_paddle_service')
    def test_cancel_subscription_endpoint_success(self, mock_get_service, client):
        """Test subscription cancellation endpoint."""
        mock_service = Mock()
        mock_service.cancel_subscription.return_value = True
        mock_get_service.return_value = mock_service
        
        response = client.post(
            '/api/payment/subscription/sub_123/cancel',
            json={'effective_date': '2024-12-31'}
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'
        assert 'cancelled' in data['message'].lower()
        
        mock_service.cancel_subscription.assert_called_once_with(
            subscription_id='sub_123',
            effective_date='2024-12-31'
        )
    
    @patch('app.payment_service.get_paddle_service')
    def test_cancel_subscription_endpoint_without_date(self, mock_get_service, client):
        """Test subscription cancellation without effective date."""
        mock_service = Mock()
        mock_service.cancel_subscription.return_value = True
        mock_get_service.return_value = mock_service
        
        response = client.post('/api/payment/subscription/sub_123/cancel',
                              json={},
                              content_type='application/json')
        
        assert response.status_code == 200
        mock_service.cancel_subscription.assert_called_once_with(
            subscription_id='sub_123',
            effective_date=None
        )
    
    @patch('app.payment_service.get_paddle_service')
    def test_cancel_subscription_endpoint_failure(self, mock_get_service, client):
        """Test subscription cancellation endpoint failure."""
        mock_service = Mock()
        mock_service.cancel_subscription.return_value = False
        mock_get_service.return_value = mock_service
        
        response = client.post('/api/payment/subscription/sub_123/cancel',
                              json={},
                              content_type='application/json')
        
        assert response.status_code == 500
        assert 'error' in response.json


class TestPaymentServiceSingleton:
    """Test the payment service singleton pattern."""
    
    @patch.dict('os.environ', {
        'PADDLE_VENDOR_ID': 'test_vendor',
        'PADDLE_API_KEY': 'test_key'
    })
    def test_get_paddle_service_singleton(self):
        """Test that get_paddle_service returns singleton instance."""
        # Reset singleton
        import app.payment_service
        app.payment_service._paddle_service = None
        
        service1 = get_paddle_service()
        service2 = get_paddle_service()
        
        assert service1 is service2
