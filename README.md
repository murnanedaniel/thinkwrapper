# ThinkWrapper Newsletter Generator

An AI-powered newsletter generation service that allows users to create and schedule automated newsletters on any topic.

## Features

- Generate AI-written newsletters using OpenAI and Anthropic Claude
- Schedule regular newsletter delivery
- Modern React frontend
- Flask API backend
- Subscription management with Paddle

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
   OPENAI_API_KEY=your-openai-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   DATABASE_URL=postgresql://username:password@localhost:5432/thinkwrapper
   SENDGRID_API_KEY=your-sendgrid-key
   PADDLE_VENDOR_ID=your-paddle-id
   PADDLE_API_KEY=your-paddle-key
   ```
   
   **Getting API Keys:**
   - **Anthropic Claude API**: Sign up at [console.anthropic.com](https://console.anthropic.com) to get your API key
   - **OpenAI API**: Get your API key from [platform.openai.com](https://platform.openai.com)
   - Store API keys securely and never commit them to source control

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
   heroku config:set OPENAI_API_KEY=your-openai-api-key
   heroku config:set ANTHROPIC_API_KEY=your-anthropic-api-key
   # etc.
   ```

4. Deploy:
   ```bash
   git push heroku main
   ```

## License

MIT 