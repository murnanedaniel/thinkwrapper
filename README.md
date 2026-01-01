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

## New: Newsletter Synthesis Service

The Newsletter Synthesis Service provides powerful backend capabilities for automated newsletter generation:

- Collect and transform source content into newsletter summaries
- AI-powered content synthesis with OpenAI integration
- Pluggable rendering system (plain text, HTML)
- Admin API endpoints for on-demand generation
- Configurable settings for schedule and delivery format
- Email distribution via SendGrid

📚 **See [NEWSLETTER_SERVICE_DOCS.md](NEWSLETTER_SERVICE_DOCS.md) for complete documentation**

🚀 **Try the demo**: `python demo_newsletter_service.py`

## Tech Stack

- **Backend**: Flask 3 + Gunicorn
- **AI Services**: OpenAI, Anthropic Claude
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
   GOOGLE_CLIENT_ID=your-google-oauth-client-id
   GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
   ```

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

4. Run the Flask development server:
   ```bash
   flask --app app run --debug
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

## Brave Search API Integration

ThinkWrapper integrates with the Brave Search API to provide web search results for newsletter content generation.

### Obtaining a Brave Search API Key

1. Visit the [Brave Search API website](https://brave.com/search/api/)
2. Sign up for a free or paid account (free tier includes up to 2,000 queries per month)
3. Navigate to your dashboard and generate an API key
4. Copy the API key for use in your environment configuration

### Configuring Brave Search API

Add your Brave Search API key to your `.env` file:

```
BRAVE_SEARCH_API_KEY=your-brave-api-key-here
```

Or set it as an environment variable in your deployment environment:

```bash
export BRAVE_SEARCH_API_KEY=your-brave-api-key-here
```

### Using Brave Search in Your Application

The Brave Search integration is available through the `search_brave()` function in `app/services.py`:

```python
from app.services import search_brave

# Basic search
results = search_brave("artificial intelligence", count=10)

# Check if search was successful
if results['success']:
    for result in results['results']:
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Description: {result['description']}")
else:
    print(f"Search failed: {results['error']}")
```

### Fallback Mechanism

The Brave Search integration includes a built-in fallback mechanism:

- **Missing API Key**: If no API key is configured, the system automatically falls back to mock search results
- **API Errors**: If the Brave API returns an error (e.g., rate limit exceeded, server error), the system falls back to mock results
- **Network Timeouts**: If the API request times out, the system falls back to mock results
- **Disable Fallback**: You can disable the fallback by setting `fallback_to_mock=False`:

```python
# No fallback - will return error if API fails
results = search_brave("query", fallback_to_mock=False)
```

### API Usage Monitoring

All Brave Search API requests and responses are automatically logged for quota monitoring:

- Request logs include: timestamp, query, and result count
- Response logs include: timestamp, status code, and query
- Logs are written using Flask's standard logging system
- Check your application logs to monitor API usage

### Testing

Run the Brave Search integration tests:

```bash
pytest tests/test_brave_search.py -v
```

The test suite includes:
- Successful API calls
- Error handling and fallback mechanisms
- Results parsing
- Logging functionality
- Mock data generation

## Anthropic Claude API Integration

This project now includes integration with the Anthropic Claude API for AI-driven natural language processing. The integration provides:

### Features

- **Synchronous text generation** - Generate text with blocking calls
- **Asynchronous text generation** - Non-blocking async/await support
- **Newsletter-specific generation** - Specialized function for newsletter content
- **Prompt formatting utilities** - Helper functions for consistent prompts
- **Response parsing** - Structured parsing of Claude API responses

### API Endpoints

#### 1. General Text Generation (`/api/claude/generate`)

Generate text using Claude API with customizable parameters.

**Request:**
```bash
curl -X POST http://localhost:5000/api/claude/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1024,
    "temperature": 1.0,
    "system_prompt": "You are a helpful science teacher"
  }'
```

**Response:**
```json
{
  "success": true,
  "text": "Quantum computing is...",
  "model": "claude-3-5-sonnet-20241022",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 150
  },
  "stop_reason": "end_turn"
}
```

#### 2. Newsletter Generation (`/api/claude/newsletter`)

Generate newsletter content with subject line and body.

**Request:**
```bash
curl -X POST http://localhost:5000/api/claude/newsletter \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI trends in 2024",
    "style": "professional",
    "max_tokens": 2000
  }'
```

**Response:**
```json
{
  "success": true,
  "subject": "Weekly AI Update: 2024 Trends",
  "content": "This week in AI...",
  "model": "claude-3-5-sonnet-20241022",
  "usage": {
    "input_tokens": 50,
    "output_tokens": 500
  }
}
```

### Using the Claude Service in Code

```python
from app import claude_service

# Synchronous text generation
result = claude_service.generate_text(
    prompt="Explain machine learning",
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    temperature=0.7
)
print(result['text'])

# Asynchronous text generation
result = await claude_service.generate_text_async(
    prompt="Explain machine learning",
    max_tokens=1024
)

# Newsletter-specific generation
newsletter = claude_service.generate_newsletter_content_claude(
    topic="Python programming",
    style="technical"
)
print(newsletter['subject'])
print(newsletter['content'])

# Format prompts with utilities
prompt = claude_service.format_prompt(
    topic="Data Science",
    style="professional",
    max_length="comprehensive"
)
```

### Available Models

- `claude-3-5-sonnet-20241022` (default) - Best balance of speed and quality
- `claude-3-opus-20240229` - Most capable model for complex tasks
- `claude-3-haiku-20240307` - Fastest model for simpler tasks

### Security Best Practices

- Store the `ANTHROPIC_API_KEY` in environment variables or a secrets manager
- Never commit API keys to source control
- Use `.env` files for local development (already in `.gitignore`)
- For production, use Heroku Config Vars or your platform's secrets management

### Testing

The Claude integration includes comprehensive tests:

```bash
# Run Claude service tests
python -m pytest tests/test_claude_service.py -v

# Run Claude route tests
python -m pytest tests/test_claude_routes.py -v

# Run all tests
python -m pytest tests/ -v
```

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
   # etc.
   ```

4. Deploy:
   ```bash
   git push heroku main
   ```

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
