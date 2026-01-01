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
   OPENAI_API_KEY=your-api-key
   DATABASE_URL=postgresql://username:password@localhost:5432/thinkwrapper
   SENDGRID_API_KEY=your-sendgrid-key
   PADDLE_VENDOR_ID=your-paddle-id
   PADDLE_API_KEY=your-paddle-key
   REDIS_URL=redis://localhost:6379/0
   ```

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
   heroku config:set OPENAI_API_KEY=your-api-key
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

ThinkWrapper uses Celery for background task processing. See [CELERY.md](CELERY.md) for detailed documentation on:

- Setting up and running Celery workers
- Available tasks (newsletter generation, email sending, etc.)
- Monitoring and troubleshooting
- Production deployment guidelines

## License

MIT 