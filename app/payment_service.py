"""
Paddle Payment Integration Service

This module handles all Paddle payment operations including:
- Payment checkout URL generation
- Webhook signature verification
- Payment status processing
- Customer and transaction management
"""

import os
import hmac
import hashlib
import json
import requests
from typing import Dict, Optional, Any
from flask import current_app
from datetime import datetime


class PaddlePaymentService:
    """Service for handling Paddle payment operations."""
    
    def __init__(self):
        """Initialize Paddle service with API credentials."""
        self.vendor_id = os.environ.get('PADDLE_VENDOR_ID')
        self.api_key = os.environ.get('PADDLE_API_KEY')
        self.webhook_secret = os.environ.get('PADDLE_WEBHOOK_SECRET')
        self.sandbox_mode = os.environ.get('PADDLE_SANDBOX', 'true').lower() == 'true'
        
        # Use sandbox or production URL based on configuration
        self.api_base_url = (
            'https://sandbox-api.paddle.com'
            if self.sandbox_mode
            else 'https://api.paddle.com'
        )
    
    def create_checkout_session(
        self,
        price_id: str,
        customer_email: str,
        success_url: str,
        cancel_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Paddle checkout session for a customer.
        
        Args:
            price_id: Paddle price ID for the product
            customer_email: Customer's email address
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            metadata: Additional metadata to attach to the transaction
            
        Returns:
            Dict containing checkout URL and session details, or None on error
        """
        if not self.vendor_id or not self.api_key:
            current_app.logger.error("Paddle credentials not configured")
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'items': [{'price_id': price_id, 'quantity': 1}],
                'customer_email': customer_email,
                'success_url': success_url,
                'custom_data': metadata or {}
            }
            
            if cancel_url:
                payload['cancel_url'] = cancel_url
            
            response = requests.post(
                f'{self.api_base_url}/checkout/session',
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                current_app.logger.info(
                    f"Created Paddle checkout session for {customer_email}"
                )
                return data
            else:
                current_app.logger.error(
                    f"Paddle checkout creation failed: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            current_app.logger.error(f"Paddle checkout error: {str(e)}")
            return None
    
    def verify_webhook_signature(
        self,
        payload: str,
        signature: str
    ) -> bool:
        """
        Verify the authenticity of a Paddle webhook using signature.
        
        Args:
            payload: Raw webhook payload as string
            signature: Paddle-Signature header value
            
        Returns:
            True if signature is valid, False otherwise
            
        Security Note:
            This verification prevents unauthorized webhook calls and ensures
            data integrity. Always verify signatures before processing webhooks.
        """
        if not self.webhook_secret:
            current_app.logger.error("Paddle webhook secret not configured")
            return False
        
        try:
            # Paddle uses HMAC-SHA256 for signature verification
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            current_app.logger.error(f"Webhook signature verification error: {str(e)}")
            return False
    
    def process_webhook_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a verified Paddle webhook event.
        
        Args:
            event_type: Type of webhook event (e.g., 'transaction.completed')
            event_data: Event data from Paddle
            
        Returns:
            Dict containing processing results and status
        """
        try:
            if event_type == 'transaction.completed':
                return self._handle_transaction_completed(event_data)
            elif event_type == 'transaction.updated':
                return self._handle_transaction_updated(event_data)
            elif event_type == 'subscription.created':
                return self._handle_subscription_created(event_data)
            elif event_type == 'subscription.updated':
                return self._handle_subscription_updated(event_data)
            elif event_type == 'subscription.cancelled':
                return self._handle_subscription_cancelled(event_data)
            elif event_type == 'subscription.past_due':
                return self._handle_subscription_past_due(event_data)
            else:
                current_app.logger.warning(f"Unhandled webhook event type: {event_type}")
                return {'status': 'unhandled', 'event_type': event_type}
                
        except Exception as e:
            current_app.logger.error(f"Webhook processing error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_transaction_completed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle completed transaction webhook."""
        transaction_id = data.get('id')
        customer_id = data.get('customer_id')
        amount = data.get('amount')
        currency = data.get('currency_code')
        
        current_app.logger.info(
            f"Transaction completed: {transaction_id} for customer {customer_id}"
        )
        
        return {
            'status': 'success',
            'event_type': 'transaction.completed',
            'transaction_id': transaction_id,
            'customer_id': customer_id,
            'amount': amount,
            'currency': currency
        }
    
    def _handle_transaction_updated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle updated transaction webhook."""
        transaction_id = data.get('id')
        status = data.get('status')
        
        current_app.logger.info(
            f"Transaction updated: {transaction_id} - status: {status}"
        )
        
        return {
            'status': 'success',
            'event_type': 'transaction.updated',
            'transaction_id': transaction_id,
            'transaction_status': status
        }
    
    def _handle_subscription_created(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new subscription webhook."""
        subscription_id = data.get('id')
        customer_id = data.get('customer_id')
        status = data.get('status')
        
        current_app.logger.info(
            f"Subscription created: {subscription_id} for customer {customer_id}"
        )
        
        return {
            'status': 'success',
            'event_type': 'subscription.created',
            'subscription_id': subscription_id,
            'customer_id': customer_id,
            'subscription_status': status
        }
    
    def _handle_subscription_updated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription update webhook."""
        subscription_id = data.get('id')
        status = data.get('status')
        
        current_app.logger.info(
            f"Subscription updated: {subscription_id} - status: {status}"
        )
        
        return {
            'status': 'success',
            'event_type': 'subscription.updated',
            'subscription_id': subscription_id,
            'subscription_status': status
        }
    
    def _handle_subscription_cancelled(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation webhook."""
        subscription_id = data.get('id')
        cancelled_at = data.get('cancelled_at')
        
        current_app.logger.info(
            f"Subscription cancelled: {subscription_id} at {cancelled_at}"
        )
        
        return {
            'status': 'success',
            'event_type': 'subscription.cancelled',
            'subscription_id': subscription_id,
            'cancelled_at': cancelled_at
        }
    
    def _handle_subscription_past_due(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle past due subscription webhook."""
        subscription_id = data.get('id')
        
        current_app.logger.warning(
            f"Subscription past due: {subscription_id}"
        )
        
        return {
            'status': 'success',
            'event_type': 'subscription.past_due',
            'subscription_id': subscription_id
        }
    
    def get_customer_info(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve customer information from Paddle.
        
        Args:
            customer_id: Paddle customer ID
            
        Returns:
            Customer data dict or None on error
        """
        if not self.api_key:
            current_app.logger.error("Paddle API key not configured")
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'{self.api_base_url}/customers/{customer_id}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(
                    f"Failed to retrieve customer: {response.status_code}"
                )
                return None
                
        except Exception as e:
            current_app.logger.error(f"Error retrieving customer: {str(e)}")
            return None
    
    def cancel_subscription(
        self,
        subscription_id: str,
        effective_date: Optional[str] = None
    ) -> bool:
        """
        Cancel a Paddle subscription.
        
        Args:
            subscription_id: Paddle subscription ID
            effective_date: When to cancel (None = immediately, or ISO date)
            
        Returns:
            True if cancellation successful, False otherwise
        """
        if not self.api_key:
            current_app.logger.error("Paddle API key not configured")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {}
            if effective_date:
                payload['effective_from'] = effective_date
            
            response = requests.post(
                f'{self.api_base_url}/subscriptions/{subscription_id}/cancel',
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                current_app.logger.info(
                    f"Subscription cancelled: {subscription_id}"
                )
                return True
            else:
                current_app.logger.error(
                    f"Failed to cancel subscription: {response.status_code}"
                )
                return False
                
        except Exception as e:
            current_app.logger.error(f"Subscription cancellation error: {str(e)}")
            return False


# Singleton instance
_paddle_service = None

def get_paddle_service() -> PaddlePaymentService:
    """Get or create the Paddle payment service singleton."""
    global _paddle_service
    if _paddle_service is None:
        _paddle_service = PaddlePaymentService()
    return _paddle_service
