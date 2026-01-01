# ThinkWrapper Newsletter Generator

An AI-powered newsletter generation service that allows users to create and schedule automated newsletters on any topic.

## Features

- Generate AI-written newsletters using OpenAI
- Schedule regular newsletter delivery
- Modern React frontend
- Flask API backend
- Subscription management with Paddle
- **Google OAuth authentication for secure login**

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
   SECRET_KEY=your-secret-key-for-sessions
   OPENAI_API_KEY=your-api-key
   DATABASE_URL=postgresql://username:password@localhost:5432/thinkwrapper
   SENDGRID_API_KEY=your-sendgrid-key
   PADDLE_VENDOR_ID=your-paddle-id
   PADDLE_API_KEY=your-paddle-key
   GOOGLE_CLIENT_ID=your-google-oauth-client-id
   GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
   ```

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
   heroku config:set OPENAI_API_KEY=your-api-key
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