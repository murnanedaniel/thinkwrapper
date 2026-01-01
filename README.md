# ThinkWrapper Newsletter Generator

An AI-powered newsletter generation service that uses Anthropic Claude and Brave Search to create and schedule automated newsletters on any topic.

## Features

- 🤖 AI-powered newsletter generation using Anthropic Claude Deep Research
- 🔍 Web research integration via Brave Search API
- 📧 Automated newsletter delivery via SendGrid
- 🔐 Google OAuth authentication
- 💳 Subscription management with Paddle
- ⚡ Async task processing with Celery
- 📱 Modern React frontend (Vite)
- 🚀 Production-ready Flask backend

## Tech Stack

- **Backend**: Flask 3 + Gunicorn
- **Database**: PostgreSQL (Supabase or Render)
- **Cache/Queue**: Redis + Celery
- **Frontend**: React 18 (Vite) SPA
- **AI**: Anthropic Claude API
- **Search**: Brave Search API
- **Email**: SendGrid
- **Auth**: Google OAuth 2.0
- **Payments**: Paddle
- **Deployment**: Render

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL (or Supabase account)
- Redis (optional for local development)

### 1. Clone and Setup

```bash
git clone https://github.com/murnanedaniel/thinkwrapper.git
cd thinkwrapper
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
# Copy template and configure
cp .env.template .env

# Edit .env and add your API keys
# See .env.template for all required variables
```

**Required API Keys:**
- `ANTHROPIC_API_KEY` - Get from [Anthropic Console](https://console.anthropic.com/)
- `BRAVE_SEARCH_API_KEY` - Get from [Brave Search API](https://brave.com/search/api/)
- `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET` - From [Google Cloud Console](https://console.cloud.google.com/)
- `DATABASE_URL` - Supabase connection string or local PostgreSQL

### 4. Database Setup

```bash
# Initialize database migrations
flask --app app db init
flask --app app db migrate -m "Initial migration"
flask --app app db upgrade
```

### 5. Run Development Server

```bash
# Terminal 1: Flask backend
flask --app app run --debug

# Terminal 2: React frontend
cd client
npm install
npm run dev

# Terminal 3 (optional): Celery worker
celery -A app.celery_app worker --loglevel=info
```

Access the app at **http://localhost:5173**

## Deployment to Render

### Automatic Deployment (Recommended)

1. Fork this repository
2. Sign up at [render.com](https://render.com)
3. Click **New → Blueprint**
4. Connect your GitHub repository
5. Render auto-detects `render.yaml` and creates:
   - Web service (Flask + React)
   - PostgreSQL database
   - Redis instance
   - Celery worker

6. Add environment variables in Render dashboard (see `.env.template`)

### Using Supabase for Database

1. Create project at [supabase.com](https://supabase.com)
2. Get connection string: Settings → Database → Connection String (URI)
3. In `render.yaml`, remove the database section
4. Set `DATABASE_URL` as secret environment variable in Render

## Development

### Running Tests

```bash
# All tests
python scripts/run_tests.py full

# Route tests only
python scripts/run_tests.py routes

# Specific test file
pytest tests/test_services.py -v
```

### Code Quality

```bash
# Format code
black app/ tests/ scripts/

# Lint
ruff check .

# Validate environment
python scripts/validate_env.py
```

### Database Migrations

```bash
# Create migration
flask --app app db migrate -m "Description"

# Apply migrations
flask --app app db upgrade

# Rollback
flask --app app db downgrade
```

## Project Structure

```
thinkwrapper/
├── app/
│   ├── __init__.py       # Flask app factory
│   ├── config.py         # Configuration classes
│   ├── models.py         # Database models
│   ├── routes.py         # API routes
│   └── services.py       # Business logic
├── client/               # React frontend
│   ├── src/
│   └── package.json
├── tests/                # Test suite
├── scripts/              # Utility scripts
├── .env.template         # Environment template
├── render.yaml           # Render deployment
└── requirements.txt      # Python dependencies
```

## Contributing

See GitHub issues for features being developed. Each issue represents a parallelizable unit of work.

### Current Development Roadmap

Major features tracked in GitHub issues:
1. Anthropic Deep Research API integration
2. Brave Search API integration
3. Newsletter synthesis service
4. Google OAuth authentication
5. Paddle payment integration
6. Celery task queue setup
7. Comprehensive test suite

## License

MIT 