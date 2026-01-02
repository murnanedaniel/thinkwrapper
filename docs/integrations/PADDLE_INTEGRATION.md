# Paddle Payment Integration Documentation

## Overview

ThinkWrapper uses Paddle for subscription billing and payment processing. This document covers the complete integration setup, testing procedures, and security considerations.

## Table of Contents

1. [Setup Instructions](#setup-instructions)
2. [Environment Configuration](#environment-configuration)
3. [Payment Flow](#payment-flow)
4. [Webhook Integration](#webhook-integration)
5. [API Endpoints](#api-endpoints)
6. [Testing](#testing)
7. [Security Notes](#security-notes)
8. [Troubleshooting](#troubleshooting)

## Setup Instructions

### 1. Paddle Account Setup

1. **Create a Paddle Account**
   - Sign up at [Paddle.com](https://paddle.com)
   - Complete business verification
   - Configure tax settings

2. **Set Up Products and Prices**
   - Go to Paddle Dashboard → Products
   - Create your subscription product(s)
   - Configure pricing tiers
   - Note the `price_id` for each tier (format: `pri_xxx`)

3. **Generate API Credentials**
   - Go to Developer Tools → Authentication
   - Create an API key
   - Save the API key securely
   - Note your Vendor ID

4. **Configure Webhook**
   - Go to Developer Tools → Webhooks
   - Add webhook URL: `https://yourdomain.com/api/payment/webhook`
   - Generate and save webhook secret
   - Select events to receive:
     - `transaction.completed`
     - `transaction.updated`
     - `subscription.created`
     - `subscription.updated`
     - `subscription.cancelled`
     - `subscription.past_due`

### 2. Application Configuration

Add the following environment variables to your application:

```bash
# Paddle Configuration
PADDLE_VENDOR_ID=your_vendor_id
PADDLE_API_KEY=your_api_key
PADDLE_WEBHOOK_SECRET=your_webhook_secret
PADDLE_SANDBOX=true  # Set to 'false' for production
```

### 3. Database Setup

Run database migrations to create payment tables:

```bash
# Create tables for users, transactions, and subscriptions
flask db upgrade
```

The integration adds the following fields to the `users` table:
- `paddle_customer_id`: Paddle's customer identifier
- `subscription_id`: Active subscription ID
- `subscription_status`: Current subscription status

And creates a new `transactions` table:
- `paddle_transaction_id`: Unique transaction ID
- `amount`, `currency`: Transaction details
- `status`: Transaction status
- `event_type`: Webhook event that created this record

## Environment Configuration

### Development (Sandbox)

```bash
PADDLE_VENDOR_ID=test_12345
PADDLE_API_KEY=test_xxxxxxxxxxxxx
PADDLE_WEBHOOK_SECRET=test_secret_key
PADDLE_SANDBOX=true
```

### Production

```bash
PADDLE_VENDOR_ID=prod_12345
PADDLE_API_KEY=live_xxxxxxxxxxxxx
PADDLE_WEBHOOK_SECRET=prod_secret_key
PADDLE_SANDBOX=false
```

⚠️ **Security Warning**: Never commit these credentials to version control. Use secure secret management services.

## Payment Flow

### Complete Payment Lifecycle

```
1. User clicks "Subscribe" button
   ↓
2. Frontend calls POST /api/payment/checkout
   ↓
3. Backend creates Paddle checkout session
   ↓
4. User redirected to Paddle checkout page
   ↓
5. User completes payment
   ↓
6. Paddle sends webhook to /api/payment/webhook
   ↓
7. Backend verifies webhook signature
   ↓
8. Backend processes payment and updates database
   ↓
9. User redirected to success page
```

### Success Flow

1. **Checkout Creation**: Application creates a checkout session with Paddle
2. **Payment Processing**: Customer completes payment on Paddle's secure checkout
3. **Webhook Notification**: Paddle sends `transaction.completed` webhook
4. **Database Update**: Application stores transaction and activates subscription
5. **Customer Redirect**: Customer redirected to success URL

### Failure Flow

1. **Payment Failure**: Payment is declined or cancelled
2. **Webhook Notification**: Paddle sends `transaction.updated` with failure status
3. **User Notification**: Application notifies user of failure
4. **Retry Option**: User can retry payment

## Webhook Integration

### Webhook Events Handled

| Event | Description | Action |
|-------|-------------|--------|
| `transaction.completed` | Payment successful | Store transaction, activate subscription |
| `transaction.updated` | Payment status changed | Update transaction status |
| `subscription.created` | New subscription | Link subscription to user |
| `subscription.updated` | Subscription changed | Update subscription details |
| `subscription.cancelled` | Subscription ended | Deactivate user access |
| `subscription.past_due` | Payment failed | Send reminder, grace period |

### Webhook Payload Example

```json
{
  "event_type": "transaction.completed",
  "event_id": "evt_xxx",
  "occurred_at": "2024-01-01T12:00:00.000Z",
  "data": {
    "id": "txn_xxx",
    "customer_id": "cus_xxx",
    "amount": "29.99",
    "currency_code": "USD",
    "status": "completed"
  }
}
```

### Webhook Signature Verification

All webhooks are verified using HMAC-SHA256:

```python
expected_signature = hmac.new(
    webhook_secret.encode('utf-8'),
    payload.encode('utf-8'),
    hashlib.sha256
).hexdigest()
```

The application automatically rejects webhooks with invalid signatures.

## API Endpoints

### POST /api/payment/checkout

Create a new checkout session for payment.

**Request:**
```json
{
  "price_id": "pri_xxx",
  "customer_email": "user@example.com",
  "success_url": "https://yoursite.com/success",
  "cancel_url": "https://yoursite.com/cancel",
  "metadata": {
    "user_id": "123"
  }
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "checkout_url": "https://checkout.paddle.com/ses_xxx",
  "session_id": "ses_xxx"
}
```

**Errors:**
- `400`: Missing required fields
- `500`: Checkout creation failed

### POST /api/payment/webhook

Receive webhook notifications from Paddle (called by Paddle, not by your application).

**Headers:**
```
Paddle-Signature: <hmac_signature>
Content-Type: application/json
```

**Response:**
- `200`: Webhook processed successfully
- `400`: Missing signature or invalid payload
- `401`: Invalid signature
- `500`: Processing error

### POST /api/payment/subscription/{subscription_id}/cancel

Cancel an active subscription.

**Request (optional):**
```json
{
  "effective_date": "2024-12-31"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Subscription cancelled"
}
```

**Errors:**
- `500`: Cancellation failed

## Testing

### Sandbox Testing

The Paddle sandbox environment allows safe testing without real payments.

#### 1. Set Up Sandbox Mode

```bash
PADDLE_SANDBOX=true
```

#### 2. Test Checkout Flow

**Manual Test:**

1. Create checkout session:
```bash
curl -X POST https://localhost:5000/api/payment/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "price_id": "pri_test_123",
    "customer_email": "test@example.com",
    "success_url": "http://localhost:5000/success",
    "cancel_url": "http://localhost:5000/cancel"
  }'
```

2. Visit the returned `checkout_url`
3. Use Paddle test cards:
   - Success: `4242 4242 4242 4242`
   - Decline: `4000 0000 0000 0002`

4. Complete checkout and verify webhook received

**Automated Test:**

```bash
# Run payment integration tests
python -m pytest tests/test_payment.py -v
```

#### 3. Test Webhook Handling

**Using Paddle's webhook simulator:**

1. Go to Paddle Dashboard → Developer Tools → Webhooks
2. Click "Send Test Webhook"
3. Select event type
4. Verify webhook received and processed

**Using curl:**

```bash
# Generate valid signature
PAYLOAD='{"event_type":"transaction.completed","data":{"id":"txn_test"}}'
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$PADDLE_WEBHOOK_SECRET" | cut -d' ' -f2)

curl -X POST https://localhost:5000/api/payment/webhook \
  -H "Content-Type: application/json" \
  -H "Paddle-Signature: $SIGNATURE" \
  -d "$PAYLOAD"
```

### Test Scenarios

| Scenario | Steps | Expected Result |
|----------|-------|-----------------|
| Successful payment | Create checkout → Complete payment | User subscription activated |
| Failed payment | Create checkout → Decline payment | User notified, no charge |
| Subscription renewal | Wait for renewal date | Automatic charge, webhook received |
| Subscription cancellation | Cancel via API | Subscription marked cancelled |
| Webhook replay attack | Send same webhook twice | Second attempt rejected |
| Invalid webhook | Send webhook with wrong signature | Webhook rejected (401) |

### Automated Test Script

```python
# tests/test_payment_integration.py
import pytest
from app import create_app
from app.payment_service import get_paddle_service

def test_complete_payment_flow():
    """Test full payment flow from checkout to webhook."""
    app = create_app({'TESTING': True})
    client = app.test_client()
    
    # 1. Create checkout
    response = client.post('/api/payment/checkout', json={
        'price_id': 'pri_test',
        'customer_email': 'test@example.com',
        'success_url': 'http://localhost/success'
    })
    assert response.status_code == 200
    
    # 2. Simulate webhook
    # ... test continues
```

## Security Notes

### Critical Security Measures

1. **Webhook Signature Verification**
   - ✅ Always verify webhook signatures
   - ✅ Use constant-time comparison (prevents timing attacks)
   - ✅ Reject webhooks with invalid signatures
   - ❌ Never skip signature verification, even in development

2. **API Key Protection**
   - ✅ Store API keys in environment variables
   - ✅ Never commit keys to version control
   - ✅ Use different keys for sandbox and production
   - ✅ Rotate keys periodically
   - ❌ Never expose keys in client-side code

3. **Webhook Endpoint Security**
   - ✅ Webhook endpoint is publicly accessible (required by Paddle)
   - ✅ Signature verification protects against unauthorized calls
   - ✅ Log all webhook attempts for monitoring
   - ⚠️ Rate limit webhook endpoint to prevent DoS

4. **Database Security**
   - ✅ Store customer IDs and transaction IDs (non-sensitive)
   - ✅ Never store full credit card numbers
   - ✅ Paddle handles all PCI compliance
   - ✅ Use encrypted connections to database

5. **HTTPS Requirements**
   - ✅ Production webhook URL must use HTTPS
   - ✅ Certificate must be valid
   - ⚠️ HTTP allowed only in local development

### Secure Configuration Checklist

- [ ] API keys stored in secure environment variables
- [ ] Webhook secret configured and verified
- [ ] HTTPS enabled for production webhook URL
- [ ] Database connections encrypted
- [ ] Logging configured for audit trail
- [ ] Rate limiting enabled on webhook endpoint
- [ ] Error messages don't expose sensitive data
- [ ] Sandbox mode disabled in production

### Common Security Pitfalls to Avoid

❌ **Don't**: Trust webhook data without signature verification  
✅ **Do**: Always verify signatures before processing

❌ **Don't**: Store API keys in code or config files  
✅ **Do**: Use environment variables or secret management services

❌ **Don't**: Use same credentials for sandbox and production  
✅ **Do**: Use separate credentials for each environment

❌ **Don't**: Process duplicate webhooks  
✅ **Do**: Implement idempotency using transaction IDs

## Troubleshooting

### Common Issues

**1. Webhook Not Received**

- Check webhook URL is correct in Paddle dashboard
- Verify endpoint is publicly accessible
- Check firewall/security group settings
- Review application logs for errors

**2. Invalid Signature Error**

- Verify webhook secret matches Paddle dashboard
- Check payload encoding (must be UTF-8)
- Ensure no middleware modifies request body
- Test with Paddle's webhook simulator

**3. Checkout Session Creation Fails**

- Verify API key is correct
- Check price_id exists in Paddle
- Ensure API key has correct permissions
- Review error response from Paddle API

**4. Subscription Not Activated**

- Check webhook was received and processed
- Verify database was updated
- Review application logs
- Check subscription status in Paddle dashboard

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Support Resources

- **Paddle Documentation**: https://developer.paddle.com
- **Paddle Support**: https://paddle.com/support
- **API Status**: https://status.paddle.com
- **Community Forum**: https://community.paddle.com

## Production Deployment

### Pre-Launch Checklist

- [ ] Test complete payment flow in sandbox
- [ ] Verify all webhook events are handled
- [ ] Test subscription cancellation
- [ ] Test payment failure scenarios
- [ ] Review security configuration
- [ ] Set up monitoring and alerts
- [ ] Document incident response procedures
- [ ] Train support team on payment issues
- [ ] Switch to production credentials
- [ ] Verify production webhook URL
- [ ] Test with small payment amount
- [ ] Monitor first production transactions

### Monitoring

Set up alerts for:
- Webhook delivery failures
- Payment processing errors
- Subscription cancellations
- Failed payment attempts
- API rate limit issues

### Maintenance

- Review transaction logs weekly
- Reconcile payments with Paddle reports monthly
- Update API integration when Paddle releases changes
- Rotate API keys every 6 months
- Review and update pricing annually

---

## Quick Reference

### Environment Variables
```bash
PADDLE_VENDOR_ID=your_vendor_id
PADDLE_API_KEY=your_api_key
PADDLE_WEBHOOK_SECRET=your_webhook_secret
PADDLE_SANDBOX=true  # or false for production
```

### Key Files
- `app/payment_service.py` - Payment service implementation
- `app/routes.py` - Payment API endpoints
- `app/models.py` - Transaction and user models
- `tests/test_payment.py` - Payment integration tests

### Support
For issues with this integration, contact the development team or create an issue in the repository.
