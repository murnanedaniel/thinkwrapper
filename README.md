# ThinkWrapper Newsletter Generator

An AI-powered newsletter generation service that allows users to create and schedule automated newsletters on any topic.

## Features

- Generate AI-written newsletters using OpenAI
- Schedule regular newsletter delivery
- Modern React frontend
- Flask API backend
- Subscription management with Paddle

## Tech Stack

- **Backend**: Flask 3 + Gunicorn
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
   OPENAI_API_KEY=your-api-key
   DATABASE_URL=postgresql://username:password@localhost:5432/thinkwrapper
   SENDGRID_API_KEY=your-sendgrid-key
   PADDLE_VENDOR_ID=your-paddle-id
   PADDLE_API_KEY=your-paddle-key
   ```

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

## Testing

ThinkWrapper has a comprehensive test suite with **36 tests** and **66% code coverage**.

### Quick Start

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_routes.py

# Generate HTML coverage report
pytest --cov-report=html
open htmlcov/index.html
```

### Test Structure

- **36 total tests** (100% passing)
- **3 test files**: routes (basic), routes (comprehensive), services
- **Routes coverage**: 100%
- **Services coverage**: 95%

For detailed testing documentation, see [TESTING.md](TESTING.md).

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
   heroku config:set OPENAI_API_KEY=your-api-key
   # etc.
   ```

4. Deploy:
   ```bash
   git push heroku main
   ```

## License

MIT 