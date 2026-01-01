# Implement Paddle Payment Integration

**Labels**: `feature`, `payments`, `subscription`, `medium-priority`

## Overview
Integrate Paddle for subscription payment processing, allowing users to subscribe to newsletter plans.

## Objectives
- Set up Paddle merchant account
- Implement subscription plans
- Handle payment webhooks
- Update user subscription status in database
- Create billing management interface

## Technical Requirements

### Paddle Setup
- [ ] Create Paddle vendor account
- [ ] Configure subscription plans in Paddle dashboard
- [ ] Set up webhook endpoint URL
- [ ] Configure webhook signature verification
- [ ] Add environment variables (already in config.py)

### Subscription Plans
Define plans in Paddle:
- [ ] Free tier (limited newsletters/month)
- [ ] Pro tier ($9.99/month - unlimited newsletters)
- [ ] Enterprise tier ($29.99/month - API access, priority support)

### Backend Implementation

#### Payment Routes
- [ ] `POST /api/paddle/checkout` - Create checkout session
- [ ] `POST /api/paddle/webhook` - Handle Paddle webhooks
- [ ] `GET /api/paddle/subscription` - Get user subscription status
- [ ] `POST /api/paddle/cancel` - Cancel subscription
- [ ] `POST /api/paddle/update` - Update payment method

#### Webhook Events to Handle
- [ ] `subscription_created` - New subscription
- [ ] `subscription_updated` - Plan change
- [ ] `subscription_cancelled` - Cancellation
- [ ] `subscription_payment_succeeded` - Successful payment
- [ ] `subscription_payment_failed` - Failed payment
- [ ] `subscription_payment_refunded` - Refund processed

#### Database Updates
- [ ] Update User.subscription_id
- [ ] Update User.subscription_status
- [ ] Create SubscriptionHistory table for audit trail
- [ ] Store plan details and billing cycle

### Frontend Implementation
- [ ] Pricing page component
- [ ] Paddle checkout integration
- [ ] Subscription management dashboard
- [ ] Payment method update UI
- [ ] Subscription status display
- [ ] Billing history view

### Security
- [ ] Verify Paddle webhook signatures (implement `verify_paddle_webhook()`)
- [ ] Validate all webhook payloads
- [ ] Rate limit checkout endpoints
- [ ] Secure sensitive data (never log payment details)
- [ ] HTTPS required for production

### Testing
- [ ] Unit tests for webhook handlers
- [ ] Test each webhook event type
- [ ] Test subscription state transitions
- [ ] Mock Paddle API for testing
- [ ] Use Paddle Sandbox for integration testing
- [ ] Test edge cases (payment failures, cancellations)

### Documentation
- [ ] Paddle integration guide
- [ ] Webhook payload examples
- [ ] Subscription flow diagrams
- [ ] API endpoint documentation
- [ ] Troubleshooting guide

## Example Implementation

```python
# app/paddle.py
import hmac
import hashlib
from flask import Blueprint, request, jsonify
from app import db
from app.models import User

paddle_bp = Blueprint('paddle', __name__, url_prefix='/api/paddle')

def verify_paddle_webhook(data, signature):
    """Verify Paddle webhook signature."""
    public_key = current_app.config['PADDLE_PUBLIC_KEY']

    # Sort data and create verification string
    sorted_data = sorted(data.items())
    verification_string = ''.join([f'{k}{v}' for k, v in sorted_data if k != 'p_signature'])

    # Verify signature
    # Note: Actual implementation requires Paddle's public key verification
    # See: https://developer.paddle.com/webhook-reference/verifying-webhooks

    return True  # Implement actual verification

@paddle_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Paddle webhooks."""
    data = request.form.to_dict()
    signature = data.get('p_signature')

    # Verify webhook signature
    if not verify_paddle_webhook(data, signature):
        return jsonify({'error': 'Invalid signature'}), 401

    alert_name = data.get('alert_name')

    if alert_name == 'subscription_created':
        handle_subscription_created(data)
    elif alert_name == 'subscription_cancelled':
        handle_subscription_cancelled(data)
    elif alert_name == 'subscription_payment_succeeded':
        handle_payment_succeeded(data)
    elif alert_name == 'subscription_payment_failed':
        handle_payment_failed(data)

    return jsonify({'success': True}), 200

def handle_subscription_created(data):
    """Handle new subscription."""
    user_email = data.get('email')
    subscription_id = data.get('subscription_id')
    plan_id = data.get('subscription_plan_id')

    user = User.query.filter_by(email=user_email).first()
    if user:
        user.subscription_id = subscription_id
        user.subscription_status = 'active'
        db.session.commit()
        logger.info(f"Subscription created for user {user.id}")

def handle_subscription_cancelled(data):
    """Handle subscription cancellation."""
    subscription_id = data.get('subscription_id')

    user = User.query.filter_by(subscription_id=subscription_id).first()
    if user:
        user.subscription_status = 'cancelled'
        db.session.commit()
        logger.info(f"Subscription cancelled for user {user.id}")

@paddle_bp.route('/checkout', methods=['POST'])
def create_checkout():
    """Create Paddle checkout session."""
    plan_id = request.json.get('plan_id')
    user_email = current_user.email

    # Return Paddle checkout URL or use Paddle.js for inline checkout
    checkout_data = {
        'vendor_id': current_app.config['PADDLE_VENDOR_ID'],
        'product_id': plan_id,
        'email': user_email,
        'passthrough': json.dumps({'user_id': current_user.id})
    }

    return jsonify(checkout_data), 200
```

## Frontend Example

```javascript
// Paddle.js integration
useEffect(() => {
  const script = document.createElement('script');
  script.src = 'https://cdn.paddle.com/paddle/paddle.js';
  script.onload = () => {
    Paddle.Setup({ vendor: PADDLE_VENDOR_ID });
  };
  document.body.appendChild(script);
}, []);

function openCheckout(planId) {
  Paddle.Checkout.open({
    product: planId,
    email: user.email,
    passthrough: JSON.stringify({ user_id: user.id }),
    successCallback: (data) => {
      console.log('Purchase complete!', data);
      window.location.href = '/dashboard';
    }
  });
}
```

## Subscription State Machine

```
none -> active (subscription_created)
active -> past_due (subscription_payment_failed)
active -> cancelled (subscription_cancelled)
past_due -> active (subscription_payment_succeeded)
past_due -> cancelled (subscription_cancelled)
```

## Acceptance Criteria
- [ ] Users can subscribe to paid plans
- [ ] Webhooks properly update database
- [ ] Webhook signatures verified
- [ ] Subscription status accurately reflected
- [ ] Users can manage/cancel subscriptions
- [ ] Tests achieve >80% coverage
- [ ] Sandbox testing complete
- [ ] Documentation complete

## Related Issues
- Depends on: #04 (Google OAuth - need authenticated users)
- Blocks: Premium features

## Estimated Effort
Medium-Large (3-4 days)

## Resources
- [Paddle Documentation](https://developer.paddle.com/)
- [Paddle Webhook Reference](https://developer.paddle.com/webhook-reference/intro)
- [Paddle Sandbox](https://developer.paddle.com/guides/how-tos/test-checkout)
