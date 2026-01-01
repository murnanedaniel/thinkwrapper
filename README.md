# ThinkWrapper Newsletter Generator

An AI-powered newsletter generation service that allows users to create and schedule automated newsletters on any topic.

## Features

- **Generate AI-written newsletters** using OpenAI
- **Newsletter Synthesis Service** - Collect, transform and synthesize content into newsletters
- **Multiple Rendering Formats** - Plain text and HTML output
- **Schedule regular newsletter delivery**
- **On-demand admin controls** for newsletter generation
- **Modern React frontend**
- **Flask API backend**
- **Subscription management** with Paddle

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