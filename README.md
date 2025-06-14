# ThinkWrapper Newsletter Generator

[![Build Status](https://github.com/murnanedaniel/thinkwrapper/workflows/Deploy%20to%20Heroku/badge.svg)](https://github.com/murnanedaniel/thinkwrapper/actions)
[![codecov](https://codecov.io/gh/murnanedaniel/thinkwrapper/branch/main/graph/badge.svg)](https://codecov.io/gh/murnanedaniel/thinkwrapper)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
   git clone https://github.com/murnanedaniel/thinkwrapper.git
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