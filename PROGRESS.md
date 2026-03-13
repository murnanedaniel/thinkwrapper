# ThinkWrapper — Progress Notes

## Goal
Close the full end-to-end loop: topic → preview → Google OAuth → pay $1/month → DB entry → email delivered.

## What Was Done

### Backend

**`app/routes.py`**
- `/api/newsletter/preview` — generates preview via Claude + Brave Search, no auth required
- `/api/newsletters` POST — creates newsletter + first issue + sends email immediately; protected by `@subscription_required`
- `/api/config` — returns `paddle_client_token`, `paddle_price_id`, `paddle_sandbox` (and vendor/product IDs) to the frontend
- `/api/payment/webhook` — handles Paddle Billing v2 webhooks; verifies HMAC-SHA256 signature with format `ts=<ts>;h1=<hash>` over `{ts}:{raw_body}`
- `/api/payment/activate-by-checkout` ← **NEW** — immediately sets `user.subscription_status = 'active'` based on the browser `checkout.completed` event. Needed because Paddle webhooks lag and the newsletter creation requires an active subscription.

**`app/payment_service.py`**
- `verify_webhook_signature` uses Paddle Billing v2 format (not Classic)
- Handles: `subscription.created`, `subscription.updated`, `subscription.canceled`, `subscription.past_due`, `transaction.completed`, `transaction.updated`
- `_find_user_by_customer` — looks up user by `paddle_customer_id` or by email from `custom_data.user_email`

**`app/constants.py`**
- `DEFAULT_FROM_EMAIL` reads from env var (Mailjet requires a verified sender — `danieltmurnane@gmail.com`)

**`app/celery_config.py`**
- Celery app lives at `app.celery_config:celery`
- Start worker: `celery -A app.celery_config:celery worker --loglevel=info`

### Frontend

**`client/src/App.jsx`**
- Initializes Paddle Billing v2: `Paddle.Environment.set('sandbox')` + `Paddle.Initialize({ token: paddle_client_token })`

**`client/src/pages/CreateNewsletter.jsx`**
- State machine: `INPUT → GENERATING → PREVIEW → NEEDS_LOGIN → NEEDS_PAYMENT → CREATING → SUCCESS`
- After `checkout.completed` event fires:
  1. Calls `/api/payment/activate-by-checkout` with `transaction_id` + `customer_id`
  2. Calls `refreshUser()`
  3. Calls `/api/newsletters` POST to create newsletter and send first issue
- Paddle checkout: `Paddle.Checkout.open({ items: [{ priceId, quantity: 1 }], customer: { email }, customData: { user_email } })`

### Credentials (in `.env`)
```
PADDLE_CLIENT_TOKEN=test_f995f0f8f38f59f3a05802fd3f1        # Billing v2 client token
PADDLE_PRICE_ID=pri_01kkkg8e492brq3fwym5pfkaqb              # $1/month recurring price
PADDLE_WEBHOOK_SECRET=pdl_ntfset_01kkkgaczjxhx19x68bm93xerk_ctd3qaf/4WNS4v1YxopjUZrpg417Z+jDY
PADDLE_SANDBOX=true
```
Note: `PADDLE_API_KEY` is the Classic vendor auth code — it doesn't work for Billing v2 API calls. We don't currently need server-side Paddle API calls (checkout is client-side, activation is via the browser event).

### Tests
- 244 tests, 82.5% coverage (threshold: 65%)
- `pytest.ini` — coverage threshold set to 65%
- Webhook signature test uses `time.time()` for current timestamp (not static — fails the 5-min tolerance check)

## What Was Verified Working
- Preview generation (Claude + Brave Search)
- Google OAuth login
- `subscription_required` correctly returns 403 when inactive
- `activate-by-checkout` sets subscription to active
- Newsletter creation + first issue saved to DB
- Email delivery via Mailjet (confirmed `send_email` returns `True`, email arrives at `danieltmurnane@gmail.com`)
- Celery worker + Redis operational

## What Still Needs a Real Browser Test

The sandbox environment can't run a browser or establish outbound tunnels (ngrok/cloudflared both fail TLS). To close the loop for real:

### Steps on Local Machine

```bash
# Pull latest
git pull origin claude/explore-business-ideas-mUqJJ

# Install deps
pip install -r requirements.txt
cd client && npm install && npm run build && cd ..

# Start services
redis-server &
celery -A app.celery_config:celery worker &
flask run  # uses .env automatically

# Optional: webhook tunnel (not required — activate-by-checkout handles it)
ngrok http 5000
# → Paddle dashboard → Notifications → update destination to https://<ngrok-url>/api/payment/webhook
```

Then open `http://localhost:5000/create`:
1. Enter a topic (e.g. "AI in Healthcare")
2. Click "Generate Preview" — wait ~10-15s for Claude + Brave
3. Click "I want this! $1/month"
4. Sign in with Google
5. Paddle checkout opens → use test card `4242 4242 4242 4242`, any future expiry, any CVV
6. After payment: `activate-by-checkout` fires → newsletter created → first issue sent to your email

### Paddle Sandbox Dashboard
- URL: https://sandbox-vendors.paddle.com
- Product: ThinkWrapper Newsletter ($1/month recurring)
- Price ID: `pri_01kkkg8e492brq3fwym5pfkaqb`
- Notification setting ID: `ntfset_01kkkgaczjxhx19x68bm93xerk`

## Known Limitations / Future Work
- No server-side Paddle API key for Billing v2 (Classic key in `.env` doesn't work for v2). Currently not needed.
- `activate-by-checkout` trusts the browser event — fine for now, but a production system should verify against Paddle API or wait for webhook
- Celery beat not running (scheduled newsletters won't fire automatically without `celery beat`)
- Google OAuth redirect URI must be configured for production domain
