"""
Paddle Payment Integration Service

Handles Paddle payment operations including:
- Webhook signature verification (Paddle Billing v2 format)
- Payment status processing with DB updates
- Checkout session creation
- Subscription management
"""

import os
import hmac
import hashlib
import time
import logging
import requests
from typing import Dict, Optional, Any
from flask import current_app

logger = logging.getLogger(__name__)


class PaddlePaymentService:
    """Service for handling Paddle payment operations."""

    def __init__(self):
        self.vendor_id = os.environ.get('PADDLE_VENDOR_ID')
        self.api_key = os.environ.get('PADDLE_API_KEY')
        self.webhook_secret = os.environ.get('PADDLE_WEBHOOK_SECRET')
        self.sandbox_mode = os.environ.get('PADDLE_SANDBOX', 'true').lower() == 'true'
        self.api_base_url = (
            'https://sandbox-api.paddle.com'
            if self.sandbox_mode
            else 'https://api.paddle.com'
        )

    def verify_webhook_signature(
        self, payload: str, signature_header: str, tolerance: int = 300
    ) -> bool:
        """
        Verify Paddle Billing v2 webhook signature.

        Paddle-Signature header format: ts=<timestamp>;h1=<hash>
        Signed payload: {timestamp}:{raw_body}
        """
        if not self.webhook_secret:
            logger.error("Paddle webhook secret not configured")
            return False

        try:
            # Parse ts=...;h1=... header
            parts = {}
            for item in signature_header.split(';'):
                if '=' in item:
                    key, value = item.split('=', 1)
                    parts[key] = value

            ts = parts.get('ts')
            h1 = parts.get('h1')

            if not ts or not h1:
                logger.error("Missing ts or h1 in Paddle-Signature header")
                return False

            # Replay attack prevention
            current_time = int(time.time())
            if abs(current_time - int(ts)) > tolerance:
                logger.error(f"Webhook timestamp too old: {ts}")
                return False

            # Build signed payload: ts:raw_body
            signed_payload = f"{ts}:{payload}"

            # Compute HMAC-SHA256
            computed = hmac.new(
                self.webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(computed, h1)

        except Exception as e:
            logger.error(f"Webhook signature verification error: {str(e)}")
            return False

    def process_webhook_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a verified Paddle webhook event and update the database."""
        from .models import User, Transaction
        db = current_app.db_session_factory()

        try:
            if event_type == 'subscription.created':
                return self._handle_subscription_created(db, event_data)
            elif event_type == 'subscription.updated':
                return self._handle_subscription_updated(db, event_data)
            elif event_type == 'subscription.canceled':
                return self._handle_subscription_cancelled(db, event_data)
            elif event_type == 'subscription.past_due':
                return self._handle_subscription_past_due(db, event_data)
            elif event_type == 'transaction.completed':
                return self._handle_transaction_completed(db, event_data)
            elif event_type == 'transaction.updated':
                return self._handle_transaction_updated(db, event_data)
            else:
                logger.warning(f"Unhandled webhook event type: {event_type}")
                return {'status': 'unhandled', 'event_type': event_type}

        except Exception as e:
            db.rollback()
            logger.error(f"Webhook processing error: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def _find_user_by_customer(self, db, event_data: Dict) -> Optional[Any]:
        """Find user by Paddle customer ID or customer email."""
        from .models import User

        customer_id = event_data.get('customer_id')
        if customer_id:
            user = db.query(User).filter_by(paddle_customer_id=customer_id).first()
            if user:
                return user

        # Try to find by email in custom_data or customer object
        custom_data = event_data.get('custom_data', {}) or {}
        email = custom_data.get('user_email')
        if not email:
            # Paddle sometimes nests customer info
            customer = event_data.get('customer', {}) or {}
            email = customer.get('email')
        if email:
            user = db.query(User).filter_by(email=email).first()
            if user:
                # Link Paddle customer ID to our user
                if customer_id and not user.paddle_customer_id:
                    user.paddle_customer_id = customer_id
                    db.commit()
                return user

        logger.error(f"Could not find user for webhook event. customer_id={customer_id}")
        return None

    def _handle_subscription_created(self, db, data: Dict) -> Dict:
        subscription_id = data.get('id')
        status = data.get('status', 'active')

        user = self._find_user_by_customer(db, data)
        if user:
            user.subscription_id = subscription_id
            user.subscription_status = status
            if data.get('customer_id'):
                user.paddle_customer_id = data['customer_id']
            db.commit()
            logger.info(f"Subscription {subscription_id} created for user {user.email}")
        else:
            logger.error(f"No user found for subscription.created: {subscription_id}")

        return {'status': 'success', 'event_type': 'subscription.created', 'subscription_id': subscription_id}

    def _handle_subscription_updated(self, db, data: Dict) -> Dict:
        subscription_id = data.get('id')
        status = data.get('status')

        user = self._find_user_by_customer(db, data)
        if user:
            user.subscription_status = status
            db.commit()
            logger.info(f"Subscription {subscription_id} updated to {status} for {user.email}")

        return {'status': 'success', 'event_type': 'subscription.updated', 'subscription_id': subscription_id}

    def _handle_subscription_cancelled(self, db, data: Dict) -> Dict:
        subscription_id = data.get('id')

        user = self._find_user_by_customer(db, data)
        if user:
            user.subscription_status = 'cancelled'
            db.commit()
            logger.info(f"Subscription {subscription_id} cancelled for {user.email}")

        return {'status': 'success', 'event_type': 'subscription.canceled', 'subscription_id': subscription_id}

    def _handle_subscription_past_due(self, db, data: Dict) -> Dict:
        subscription_id = data.get('id')

        user = self._find_user_by_customer(db, data)
        if user:
            user.subscription_status = 'past_due'
            db.commit()
            logger.warning(f"Subscription {subscription_id} past due for {user.email}")

        return {'status': 'success', 'event_type': 'subscription.past_due', 'subscription_id': subscription_id}

    def _handle_transaction_completed(self, db, data: Dict) -> Dict:
        from .models import Transaction

        transaction_id = data.get('id')
        customer_id = data.get('customer_id')
        subscription_id = data.get('subscription_id')

        # Extract amount from details
        details = data.get('details', {}) or {}
        totals = details.get('totals', {}) or {}
        amount = totals.get('grand_total', '0')
        currency = data.get('currency_code', 'USD')

        user = self._find_user_by_customer(db, data)
        if user:
            # Check for duplicate transaction
            existing = db.query(Transaction).filter_by(paddle_transaction_id=transaction_id).first()
            if not existing:
                txn = Transaction(
                    user_id=user.id,
                    paddle_transaction_id=transaction_id,
                    paddle_subscription_id=subscription_id,
                    amount=int(amount) / 100 if amount else 0,
                    currency=currency,
                    status='completed',
                    event_type='transaction.completed'
                )
                db.add(txn)
                db.commit()
                logger.info(f"Transaction {transaction_id} recorded for {user.email}")

        return {'status': 'success', 'event_type': 'transaction.completed', 'transaction_id': transaction_id}

    def _handle_transaction_updated(self, db, data: Dict) -> Dict:
        from .models import Transaction

        transaction_id = data.get('id')
        status = data.get('status')

        existing = db.query(Transaction).filter_by(paddle_transaction_id=transaction_id).first()
        if existing:
            existing.status = status
            db.commit()

        return {'status': 'success', 'event_type': 'transaction.updated', 'transaction_id': transaction_id}

    def create_checkout_session(self, price_id, customer_email, success_url, cancel_url=None, metadata=None):
        if not self.vendor_id or not self.api_key:
            logger.error("Paddle credentials not configured")
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
                headers=headers, json=payload, timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Paddle checkout failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Paddle checkout error: {str(e)}")
            return None

    def cancel_subscription(self, subscription_id, effective_date=None):
        if not self.api_key:
            return False
        try:
            headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
            payload = {}
            if effective_date:
                payload['effective_from'] = effective_date
            response = requests.post(
                f'{self.api_base_url}/subscriptions/{subscription_id}/cancel',
                headers=headers, json=payload, timeout=10
            )
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Subscription cancellation error: {str(e)}")
            return False


_paddle_service = None

def get_paddle_service() -> PaddlePaymentService:
    global _paddle_service
    if _paddle_service is None:
        _paddle_service = PaddlePaymentService()
    return _paddle_service
