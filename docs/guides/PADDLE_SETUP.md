# Paddle Payments Sandbox Setup Guide

This guide walks you through setting up Paddle Payments in sandbox mode for testing.

## Prerequisites

- A Paddle account (sign up at [paddle.com](https://paddle.com))
- Access to the Paddle Sandbox environment

## Quick Setup Steps

### 1. Access Paddle Sandbox

1. Log in to your Paddle account
2. Navigate to the **Sandbox** environment using the environment switcher in the top navigation
3. Alternatively, visit: [https://sandbox-vendors.paddle.com](https://sandbox-vendors.paddle.com)

### 2. Get Your Vendor ID

1. In the Paddle dashboard, click on **Developer Tools** in the left sidebar
2. Click on **Authentication**
3. Your **Vendor ID** (or Seller ID) will be displayed at the top
4. Copy this value - you'll need it for `PADDLE_VENDOR_ID`

### 3. Generate API Key

1. In **Developer Tools** → **Authentication**
2. Click **Generate API Key** or **Create API Key**
3. Give it a descriptive name (e.g., "ThinkWrapper Sandbox")
4. Set appropriate permissions:
   - ✅ Read transactions
   - ✅ Write transactions
   - ✅ Read subscriptions
   - ✅ Write subscriptions
   - ✅ Read customers
   - ✅ Write customers
5. Click **Create** and copy the API key
6. **Important**: Save this key immediately - you won't be able to see it again
7. This is your `PADDLE_API_KEY`

### 4. Create a Test Product

1. Go to **Products** → **Products**
2. Click **Add Product**
3. Enter product details:
   - Name: "ThinkWrapper Subscription"
   - Description: "Monthly subscription for ThinkWrapper"
   - Tax category: Select appropriate category
4. Click **Save Product**

### 5. Create a Price

1. After creating the product, click **Add Price**
2. Configure the price:
   - Billing cycle: Monthly (or your preferred cycle)
   - Price: $29.99 USD (or your preferred amount)
   - Trial period: Optional (e.g., 7 days free)
3. Click **Save Price**
4. Copy the **Price ID** (format: `pri_xxxxx`) - you'll use this in API calls

### 6. Configure Webhook

1. Go to **Developer Tools** → **Webhooks**
2. Click **Add Webhook** or **Create Webhook Endpoint**
3. Enter your webhook URL:
   - Local testing: Use [ngrok](https://ngrok.com) or similar tunneling service
   - Example: `https://your-domain.ngrok.io/api/payment/webhook`
4. Select events to receive:
   - ✅ `transaction.completed`
   - ✅ `transaction.updated`
   - ✅ `subscription.created`
   - ✅ `subscription.updated`
   - ✅ `subscription.cancelled`
   - ✅ `subscription.past_due`
5. Click **Save Webhook**
6. Copy the **Webhook Secret** - this is your `PADDLE_WEBHOOK_SECRET`

### 7. Configure Environment Variables

1. Copy `.env.example` to `.env` in your project root:
   ```bash
   cp .env.example .env
   ```

2. Update the Paddle configuration in `.env`:
   ```bash
   PADDLE_VENDOR_ID=12345  # Your vendor ID from step 2
   PADDLE_API_KEY=your_api_key_here  # API key from step 3
   PADDLE_WEBHOOK_SECRET=your_webhook_secret_here  # Webhook secret from step 6
   PADDLE_SANDBOX=true  # Keep as 'true' for sandbox testing
   ```

3. **Never commit `.env` to git** - it's already in `.gitignore`

## Testing Your Setup

### Test 1: Verify Credentials

Run the Python REPL to test your configuration:

```python
python
>>> import os
>>> from dotenv import load_dotenv
>>> load_dotenv()
>>> os.getenv('PADDLE_VENDOR_ID')
'12345'  # Should show your vendor ID
>>> os.getenv('PADDLE_API_KEY')
'your_api_key...'  # Should show your API key
```

### Test 2: Create Test Checkout

Use curl to test checkout creation:

```bash
# Start your Flask app first
python app.py  # or flask run

# In another terminal:
curl -X POST http://localhost:5000/api/payment/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "price_id": "pri_xxxxx",
    "customer_email": "test@example.com",
    "success_url": "http://localhost:5000/success",
    "cancel_url": "http://localhost:5000/cancel"
  }'
```

Expected response:
```json
{
  "status": "success",
  "data": {
    "checkout_url": "https://sandbox-checkout.paddle.com/checkout?_checkout_id=...",
    "session_id": "ses_xxxxx"
  }
}
```

### Test 3: Test Webhook Delivery

#### Option A: Use ngrok for Local Testing

1. Install ngrok: https://ngrok.com/download
2. Start your Flask app on port 5000
3. In another terminal, run:
   ```bash
   ngrok http 5000
   ```
4. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
5. Update your webhook URL in Paddle dashboard to: `https://abc123.ngrok.io/api/payment/webhook`
6. Use Paddle's webhook testing tool to send a test webhook

#### Option B: Use Paddle's Webhook Simulator

1. Go to **Developer Tools** → **Webhooks** in Paddle dashboard
2. Click your webhook endpoint
3. Click **Send Test Event**
4. Select event type (e.g., `transaction.completed`)
5. Click **Send Test**
6. Check your application logs to verify webhook was received

### Test 4: Complete Test Payment

1. Visit the `checkout_url` from Test 2
2. Use Paddle's test card numbers:
   - **Success**: `4242 4242 4242 4242`
   - **Decline**: `4000 0000 0000 0002`
3. Use any future expiry date and any CVV
4. Complete the checkout
5. Verify webhook was received in your application logs

### Test 5: Run Automated Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run payment tests
python -m pytest tests/test_payment.py -v

# Run with coverage
python -m pytest tests/test_payment.py --cov=app/payment_service --cov-report=term-missing
```

## Common Issues and Solutions

### Issue: "Invalid API Key" Error

**Solution**: 
- Verify you copied the entire API key
- Check you're using sandbox key for sandbox mode
- Ensure no extra spaces in `.env` file
- Try generating a new API key

### Issue: Webhook Not Received

**Solutions**:
- Verify webhook URL is publicly accessible (use ngrok for local testing)
- Check webhook URL in Paddle dashboard is correct
- Ensure your Flask app is running
- Check firewall/security group settings
- Review application logs for errors

### Issue: Signature Verification Failed

**Solutions**:
- Verify webhook secret matches Paddle dashboard
- Ensure no middleware is modifying request body
- Check logs for actual signature vs expected signature
- Try regenerating webhook secret in Paddle dashboard

### Issue: Checkout URL Not Working

**Solutions**:
- Verify price_id exists and is active
- Check product is enabled in Paddle dashboard
- Ensure API key has correct permissions
- Try creating checkout directly in Paddle dashboard

## Next Steps

Once sandbox testing is complete:

1. **Review Security**: Check out [../integrations/PADDLE_INTEGRATION.md](../integrations/PADDLE_INTEGRATION.md) for security best practices
2. **Add Integration Tests**: Implement full flow integration tests
3. **Production Setup**: Switch to production credentials when ready
4. **Monitor**: Set up logging and monitoring for payment events

## Support Resources

- 📚 [Full Paddle Integration Docs](../integrations/PADDLE_INTEGRATION.md)
- 🔧 [Paddle Developer Documentation](https://developer.paddle.com)
- 💬 [Paddle Community Forum](https://community.paddle.com)
- 🆘 [Paddle Support](https://paddle.com/support)

## Security Reminders

⚠️ **Important Security Notes:**

- Never commit `.env` file to version control
- Never share API keys or webhook secrets
- Use different credentials for sandbox and production
- Rotate API keys periodically (recommended: every 6 months)
- Always verify webhook signatures before processing
- Use HTTPS for production webhook URLs

---

**Need Help?** If you encounter issues not covered here, check the [troubleshooting section](../integrations/PADDLE_INTEGRATION.md#troubleshooting) in the full integration documentation.
