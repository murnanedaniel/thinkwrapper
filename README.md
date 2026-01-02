# ThinkWrapper Newsletter Generator

An AI-powered newsletter generation service that allows users to create and schedule automated newsletters on any topic.

## Features

- **Generate AI-written newsletters** using OpenAI and Anthropic Claude
- **Newsletter Synthesis Service** - Collect, transform and synthesize content into newsletters
- **Multiple Rendering Formats** - Plain text and HTML output
- **Web search integration with Brave Search API**
- **Schedule regular newsletter delivery**
- **On-demand admin controls** for newsletter generation
- **Modern React frontend**
- **Flask API backend**
- **Subscription management** with Paddle
- **Google OAuth authentication for secure login**
- **Background task processing** with Celery and Redis

## Documentation

| Document | Description |
|----------|-------------|
| [User Journeys](docs/USER_JOURNEYS.md) | Complete user flow documentation |
| [Newsletter Service](docs/guides/NEWSLETTER_SERVICE_DOCS.md) | Service architecture & API reference |
| [Testing Guide](docs/guides/TESTING.md) | Test suite documentation |
| [Implementation Summary](docs/guides/IMPLEMENTATION_SUMMARY.md) | Architecture overview |

### Integration Guides

| Integration | Guide |
|-------------|-------|
| Brave Search | [docs/integrations/BRAVE_SEARCH_INTEGRATION.md](docs/integrations/BRAVE_SEARCH_INTEGRATION.md) |
| Celery Tasks | [docs/integrations/CELERY.md](docs/integrations/CELERY.md) |
| Google OAuth | [docs/integrations/GOOGLE_OAUTH_SETUP.md](docs/integrations/GOOGLE_OAUTH_SETUP.md) |
| Paddle Payments | [docs/integrations/PADDLE_INTEGRATION.md](docs/integrations/PADDLE_INTEGRATION.md) |

## Tech Stack

- **Backend**: Flask 3 + Gunicorn
- **AI Services**: OpenAI, Anthropic Claude
- **Task Queue**: Celery with Redis
- **Database**: PostgreSQL
- **Frontend**: React 18 (Vite) SPA
- **Email**: SendGrid
- **Payments**: Paddle
- **Deployment**: Heroku

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL (local or remote instance)
- Redis (for Celery task queue)

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/thinkwrapper.git
   cd thinkwrapper
   ```

2. Create a Python virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables (create a `.env` file in project root):
   ```
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-for-sessions
   OPENAI_API_KEY=your-openai-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   BRAVE_SEARCH_API_KEY=your-brave-api-key
   DATABASE_URL=postgresql://username:password@localhost:5432/thinkwrapper
   SENDGRID_API_KEY=your-sendgrid-key
   PADDLE_VENDOR_ID=your-paddle-id
   PADDLE_API_KEY=your-paddle-key
   PADDLE_WEBHOOK_SECRET=your-webhook-secret
   PADDLE_SANDBOX=true
   GOOGLE_CLIENT_ID=your-google-oauth-client-id
   GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
   REDIS_URL=redis://localhost:6379/0
   ```

   For detailed Paddle setup instructions, see [docs/integrations/PADDLE_INTEGRATION.md](docs/integrations/PADDLE_INTEGRATION.md)

   **Getting API Keys:**
   - **Anthropic Claude API**: Sign up at [console.anthropic.com](https://console.anthropic.com) to get your API key
   - **OpenAI API**: Get your API key from [platform.openai.com](https://platform.openai.com)
   - Store API keys securely and never commit them to source control

### Google OAuth Setup

To enable Google OAuth authentication:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to "Credentials" and create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - Development: `http://localhost:5000/api/auth/callback`
   - Production: `https://your-domain.com/api/auth/callback`
6. Copy the Client ID and Client Secret to your `.env` file

**Note:** For production, ensure you have a secure `SECRET_KEY` for session management.

4. Install and start Redis (required for Celery):
   ```bash
   # macOS
   brew install redis
   brew services start redis

   # Ubuntu/Debian
   sudo apt-get install redis-server
   sudo systemctl start redis
   ```

5. Run the Flask development server:
   ```bash
   flask --app app run --debug
   ```

6. Start Celery worker (in a separate terminal):
   ```bash
   python celery_worker.py worker --loglevel=info
   ```

7. (Optional) Start Celery beat for periodic tasks (in another terminal):
   ```bash
   python celery_worker.py beat --loglevel=info
   ```

### Frontend Setup

1. Install frontend dependencies:
   ```bash
   cd client
   npm install
   ```

2. Start the Vite development server:
   ```bash
   npm run dev
   ```

3. Access the frontend at http://localhost:5173

## Testing

ThinkWrapper has a comprehensive test suite covering all major functionality.

### Quick Start

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run journey tests only
pytest tests/test_journeys.py -v

# Generate coverage report
pytest --cov=app --cov-report=html
```

### Test Structure

```
tests/
├── test_journeys.py      # End-to-end user journey tests (36 tests)
├── test_routes.py        # Basic route tests
├── test_services.py      # Service layer tests
├── test_auth.py          # Authentication tests
├── test_payment.py       # Payment integration tests
└── ...                   # Additional test files
```

For detailed testing documentation, see [docs/guides/TESTING.md](docs/guides/TESTING.md).

## Deployment

The app is configured for Heroku deployment:

1. Create a Heroku app:
   ```bash
   heroku create thinkwrapper-app
   ```

2. Add required add-ons:
   ```bash
   heroku addons:create heroku-postgresql:mini
   heroku addons:create sendgrid:starter
   heroku addons:create heroku-redis:mini
   ```

3. Set environment variables:
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=your-production-secret-key
   heroku config:set OPENAI_API_KEY=your-openai-api-key
   heroku config:set ANTHROPIC_API_KEY=your-anthropic-api-key
   heroku config:set BRAVE_SEARCH_API_KEY=your-brave-api-key
   heroku config:set GOOGLE_CLIENT_ID=your-google-client-id
   heroku config:set GOOGLE_CLIENT_SECRET=your-google-client-secret
   heroku config:set PADDLE_VENDOR_ID=your-paddle-vendor-id
   heroku config:set PADDLE_API_KEY=your-paddle-api-key
   heroku config:set PADDLE_WEBHOOK_SECRET=your-paddle-webhook-secret
   # etc.
   ```

4. Deploy:
   ```bash
   git push heroku main
   ```

5. Scale worker dynos:
   ```bash
   heroku ps:scale web=1 worker=1 beat=1
   ```

## Background Tasks

ThinkWrapper uses Celery for background task processing. See [docs/integrations/CELERY.md](docs/integrations/CELERY.md) for detailed documentation on:

- Setting up and running Celery workers
- Available tasks (newsletter generation, email sending, etc.)
- Monitoring and troubleshooting
- Production deployment guidelines

## Troubleshooting

### Google OAuth Issues

**Problem:** "redirect_uri_mismatch" error
- **Solution:** Ensure the redirect URI in your Google Cloud Console matches exactly with your application URL. For local development, use `http://localhost:5000/api/auth/callback`.

**Problem:** Users can't log in after deployment
- **Solution:**
  1. Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in production environment
  2. Ensure your production URL is added as an authorized redirect URI in Google Cloud Console
  3. Check that `SECRET_KEY` is set for session management

**Problem:** "Invalid client" error
- **Solution:** Double-check that your Google OAuth credentials are correctly copied to your environment variables without any extra spaces or characters.

**Problem:** Session not persisting after login
- **Solution:** Ensure `SECRET_KEY` is set in your environment variables. In production, this should be a strong, random string.

### Database Issues

**Problem:** User table doesn't have oauth_provider column
- **Solution:** Run database migrations or manually add the columns:
  ```sql
  ALTER TABLE users ADD COLUMN name VARCHAR(255);
  ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(50);
  ALTER TABLE users ADD COLUMN oauth_id VARCHAR(255);
  ```

## License

MIT
