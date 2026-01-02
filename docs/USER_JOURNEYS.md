# User Journeys

This document describes the complete user journeys for ThinkWrapper Newsletter Generator, including the expected flow, API calls, and success criteria.

## Table of Contents

1. [User Signup Journey](#1-user-signup-journey)
2. [Newsletter Creation Journey](#2-newsletter-creation-journey)
3. [Newsletter Generation Journey](#3-newsletter-generation-journey)
4. [Payment & Subscription Journey](#4-payment--subscription-journey)
5. [Newsletter Preview Journey](#5-newsletter-preview-journey)

---

## 1. User Signup Journey

### Overview
New users authenticate via Google OAuth to access the application.

### Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        SIGNUP JOURNEY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User visits homepage ──> 2. Clicks "Sign in with Google"   │
│                              │                                  │
│                              ▼                                  │
│  3. GET /api/auth/login ──> Redirects to Google OAuth          │
│                              │                                  │
│                              ▼                                  │
│  4. User authenticates with Google                              │
│                              │                                  │
│                              ▼                                  │
│  5. GET /api/auth/callback ──> Creates/updates user record     │
│                              │                                  │
│                              ▼                                  │
│  6. User redirected to dashboard (authenticated)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### API Endpoints

| Step | Endpoint | Method | Description |
|------|----------|--------|-------------|
| 3 | `/api/auth/login` | GET | Initiates OAuth flow, redirects to Google |
| 5 | `/api/auth/callback` | GET | Handles OAuth callback, creates session |
| - | `/api/auth/user` | GET | Returns current user info |
| - | `/api/auth/logout` | GET | Logs out user, clears session |

### Success Criteria

- [ ] User is redirected to Google OAuth consent screen
- [ ] After authentication, user record is created in database
- [ ] User session is established
- [ ] `/api/auth/user` returns `authenticated: true` with user data

### Test Script

```bash
# Check if user endpoint returns authenticated status
curl -X GET http://localhost:5000/api/auth/user

# Expected response (unauthenticated):
# {"authenticated": false}

# After OAuth flow, expected response:
# {"authenticated": true, "email": "user@example.com", "name": "User Name", "id": 1}
```

---

## 2. Newsletter Creation Journey

### Overview
Authenticated users create a new newsletter by specifying topic and schedule.

### Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   NEWSLETTER CREATION JOURNEY                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User navigates to /create page                              │
│                              │                                  │
│                              ▼                                  │
│  2. User fills form:                                            │
│     - Newsletter name                                           │
│     - Topic (e.g., "AI Trends")                                 │
│     - Schedule (daily/weekly/biweekly/monthly)                  │
│                              │                                  │
│                              ▼                                  │
│  3. POST /api/generate with topic and style                     │
│                              │                                  │
│                              ▼                                  │
│  4. Server queues Celery task, returns task_id                  │
│                              │                                  │
│                              ▼                                  │
│  5. Frontend polls GET /api/task/{task_id}                      │
│                              │                                  │
│                              ▼                                  │
│  6. Task completes, content returned to user                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### API Endpoints

| Step | Endpoint | Method | Payload | Description |
|------|----------|--------|---------|-------------|
| 3 | `/api/generate` | POST | `{"topic": "AI Trends", "style": "professional"}` | Queue newsletter generation |
| 5 | `/api/task/{task_id}` | GET | - | Check task status |

### Request/Response Examples

**Generate Newsletter Request:**
```json
POST /api/generate
Content-Type: application/json

{
  "topic": "Artificial Intelligence Trends",
  "style": "professional"
}
```

**Generate Newsletter Response (202 Accepted):**
```json
{
  "success": true,
  "status": "processing",
  "task_id": "abc123-def456",
  "message": "Generating newsletter about 'Artificial Intelligence Trends'"
}
```

**Task Status Response (Pending):**
```json
{
  "state": "PENDING",
  "status": "Task is waiting to be processed"
}
```

**Task Status Response (Success):**
```json
{
  "state": "SUCCESS",
  "result": {
    "subject": "AI Trends: Weekly Digest",
    "content": "Newsletter content here..."
  }
}
```

### Success Criteria

- [ ] Topic passes validation (3-500 characters, no injection)
- [ ] Style is valid (professional, casual, technical, concise)
- [ ] Task is queued and task_id returned
- [ ] Task status can be polled
- [ ] Generated content includes subject and body

### Input Validation

| Field | Rules |
|-------|-------|
| `topic` | Required, 3-500 chars, no script injection |
| `style` | Optional, must be: professional, casual, technical, concise |

---

## 3. Newsletter Generation Journey (Admin)

### Overview
Administrators can trigger on-demand newsletter synthesis with advanced options.

### Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                 ADMIN NEWSLETTER SYNTHESIS                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Admin sends POST /api/admin/synthesize                      │
│     with newsletter_id, topic, style, format                    │
│                              │                                  │
│                              ▼                                  │
│  2. Server collects source content                              │
│                              │                                  │
│                              ▼                                  │
│  3. AI synthesizes newsletter (OpenAI/Claude)                   │
│                              │                                  │
│                              ▼                                  │
│  4. Content rendered in requested format (HTML/text/both)       │
│                              │                                  │
│                              ▼                                  │
│  5. Optionally sends email via SendGrid                         │
│                              │                                  │
│                              ▼                                  │
│  6. Returns synthesized content with metadata                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/synthesize` | POST | Generate and optionally send newsletter |
| `/api/admin/newsletter/config` | GET/POST | Get/update newsletter config |
| `/api/admin/newsletter/preview` | POST | Preview without sending |

### Request/Response Examples

**Synthesize Request:**
```json
POST /api/admin/synthesize
Content-Type: application/json

{
  "newsletter_id": 1,
  "topic": "AI Weekly Update",
  "style": "professional",
  "format": "both",
  "send_email": true,
  "email_to": "subscriber@example.com"
}
```

**Synthesize Response:**
```json
{
  "success": true,
  "data": {
    "subject": "AI Weekly Update - January 2, 2026",
    "content": "Raw content here...",
    "rendered": {
      "html": "<html>...</html>",
      "text": "Plain text version..."
    },
    "metadata": {
      "content_items_count": 2,
      "generated_at": "2026-01-02T12:00:00Z",
      "style": "professional",
      "format": "both",
      "email_sent": true
    }
  }
}
```

### Success Criteria

- [ ] Newsletter ID and topic are validated
- [ ] Style and format are validated
- [ ] Content is synthesized successfully
- [ ] Rendered output matches requested format
- [ ] Email sent if requested (with valid email)

---

## 4. Payment & Subscription Journey

### Overview
Users subscribe to premium features via Paddle payment integration.

### Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PAYMENT JOURNEY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User clicks "Subscribe" on pricing page                     │
│                              │                                  │
│                              ▼                                  │
│  2. POST /api/payment/checkout                                  │
│     with price_id, email, success_url                           │
│                              │                                  │
│                              ▼                                  │
│  3. Server creates Paddle checkout session                      │
│                              │                                  │
│                              ▼                                  │
│  4. User redirected to Paddle checkout page                     │
│                              │                                  │
│                              ▼                                  │
│  5. User completes payment on Paddle                            │
│                              │                                  │
│                              ▼                                  │
│  6. Paddle sends webhook to /api/payment/webhook                │
│     (transaction.completed event)                               │
│                              │                                  │
│                              ▼                                  │
│  7. Server verifies signature, updates user subscription        │
│                              │                                  │
│                              ▼                                  │
│  8. User gains access to premium features                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/payment/checkout` | POST | Create Paddle checkout session |
| `/api/payment/webhook` | POST | Handle Paddle webhook events |
| `/api/payment/subscription/{id}/cancel` | POST | Cancel subscription |

### Request/Response Examples

**Checkout Request:**
```json
POST /api/payment/checkout
Content-Type: application/json

{
  "price_id": "pri_monthly_9",
  "customer_email": "user@example.com",
  "success_url": "https://app.thinkwrapper.com/success",
  "cancel_url": "https://app.thinkwrapper.com/pricing"
}
```

**Checkout Response:**
```json
{
  "success": true,
  "data": {
    "checkout_url": "https://checkout.paddle.com/...",
    "session_id": "ses_abc123"
  }
}
```

**Webhook Event (transaction.completed):**
```json
{
  "event_type": "transaction.completed",
  "data": {
    "id": "txn_abc123",
    "customer_id": "cus_xyz789",
    "amount": "9.00",
    "currency_code": "USD"
  }
}
```

### Webhook Events Handled

| Event | Description |
|-------|-------------|
| `transaction.completed` | Payment successful |
| `transaction.updated` | Transaction status changed |
| `subscription.created` | New subscription created |
| `subscription.updated` | Subscription modified |
| `subscription.cancelled` | Subscription cancelled |
| `subscription.past_due` | Payment overdue |

### Success Criteria

- [ ] Checkout session created with valid URL
- [ ] Webhook signature verified (HMAC-SHA256)
- [ ] Transaction events processed correctly
- [ ] Subscription status updated in database
- [ ] Cancellation works correctly

---

## 5. Newsletter Preview Journey

### Overview
Users can preview newsletter content in different formats before sending.

### Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PREVIEW JOURNEY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User has newsletter content ready                           │
│                              │                                  │
│                              ▼                                  │
│  2. POST /api/admin/newsletter/preview                          │
│     with subject, content, format                               │
│                              │                                  │
│                              ▼                                  │
│  3. Server renders content in requested format                  │
│                              │                                  │
│                              ▼                                  │
│  4. Rendered preview returned to user                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Request/Response Examples

**Preview Request:**
```json
POST /api/admin/newsletter/preview
Content-Type: application/json

{
  "subject": "Weekly AI Digest",
  "content": "# Welcome\n\nThis week in AI...",
  "format": "both"
}
```

**Preview Response:**
```json
{
  "success": true,
  "data": {
    "rendered": {
      "html": "<!DOCTYPE html>...",
      "text": "Subject: Weekly AI Digest\n======\n..."
    }
  }
}
```

### Success Criteria

- [ ] Subject and content validated
- [ ] Format validated (html, text, both)
- [ ] Markdown converted to HTML correctly
- [ ] Plain text version generated

---

## Claude API Integration

### Overview
Alternative AI generation using Anthropic Claude API.

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/claude/generate` | POST | Generate generic text |
| `/api/claude/newsletter` | POST | Generate newsletter content |

### Request Examples

**Claude Text Generation:**
```json
POST /api/claude/generate
Content-Type: application/json

{
  "prompt": "Explain quantum computing in simple terms",
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 1024,
  "temperature": 0.7
}
```

**Claude Newsletter Generation:**
```json
POST /api/claude/newsletter
Content-Type: application/json

{
  "topic": "Machine Learning Trends",
  "style": "technical",
  "max_tokens": 2000
}
```

---

## Error Handling

All API endpoints return standardized error responses:

```json
{
  "success": false,
  "error": "Error message here",
  "details": "Optional additional details"
}
```

### Common Error Codes

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid signature/token |
| 415 | Unsupported Media Type - Not JSON |
| 500 | Internal Server Error |

---

## Environment Variables Required

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | For OpenAI generation |
| `ANTHROPIC_API_KEY` | Anthropic API key | For Claude generation |
| `SENDGRID_API_KEY` | SendGrid API key | For email sending |
| `BRAVE_SEARCH_API_KEY` | Brave Search API key | For content search |
| `PADDLE_VENDOR_ID` | Paddle vendor ID | For payments |
| `PADDLE_API_KEY` | Paddle API key | For payments |
| `PADDLE_WEBHOOK_SECRET` | Paddle webhook secret | For webhook verification |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | For authentication |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | For authentication |
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `REDIS_URL` | Redis connection URL | For Celery tasks |
