# Google OAuth Setup Guide

This guide will help you set up Google OAuth authentication for ThinkWrapper.

## Prerequisites

- Google Cloud account
- ThinkWrapper application running locally or deployed

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a Project" → "New Project"
3. Enter a project name (e.g., "ThinkWrapper")
4. Click "Create"

## Step 2: Enable Google+ API

1. In your project dashboard, navigate to "APIs & Services" → "Library"
2. Search for "Google+ API" or "Google Identity"
3. Click on it and press "Enable"

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" user type
3. Fill in the required fields:
   - **App name**: ThinkWrapper
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Click "Save and Continue"
5. Add scopes (optional) - the default scopes are sufficient
6. Click "Save and Continue"
7. Add test users if needed for development
8. Click "Save and Continue"

## Step 4: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Choose "Web application" as the application type
4. Enter a name (e.g., "ThinkWrapper Web Client")
5. Add Authorized redirect URIs:
   - For local development: `http://localhost:5000/api/auth/callback`
   - For production: `https://your-domain.com/api/auth/callback`
6. Click "Create"
7. Copy the **Client ID** and **Client Secret**

## Step 5: Configure Environment Variables

Add the following to your `.env` file:

```bash
# Required for session management
SECRET_KEY=your-random-secret-key-here

# Google OAuth credentials
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://username:password@localhost:5432/thinkwrapper
```

**Important:** 
- Generate a strong, random `SECRET_KEY` for production
- Never commit your `.env` file to version control
- Keep your `GOOGLE_CLIENT_SECRET` secure

## Step 6: Test the Integration

1. Start your Flask application:
   ```bash
   flask --app app run --debug
   ```

2. Navigate to `http://localhost:5000/login` in your browser

3. Click "Continue with Google"

4. You should be redirected to Google's login page

5. After successful authentication, you'll be redirected back to your app

## Troubleshooting

### Error: "redirect_uri_mismatch"

**Cause:** The redirect URI in your request doesn't match the one configured in Google Cloud Console.

**Solution:** 
- Ensure the redirect URI exactly matches what's configured in Google Cloud Console
- Check for trailing slashes
- Verify the protocol (http vs https)

### Error: "Invalid client"

**Cause:** The client ID or client secret is incorrect.

**Solution:**
- Double-check that you copied the credentials correctly
- Ensure there are no extra spaces or characters
- Regenerate credentials if needed

### Users Can't Log In After Deployment

**Cause:** Production URL not added as authorized redirect URI.

**Solution:**
- Add your production URL to the authorized redirect URIs in Google Cloud Console
- Wait a few minutes for changes to propagate
- Clear browser cache and try again

### Session Not Persisting

**Cause:** `SECRET_KEY` is not set or is changing between requests.

**Solution:**
- Ensure `SECRET_KEY` is set in your environment variables
- Use a consistent, strong secret key in production
- For Heroku: `heroku config:set SECRET_KEY=your-secret-key`

## Production Deployment

When deploying to production (e.g., Heroku):

1. Set environment variables:
   ```bash
   heroku config:set SECRET_KEY=your-production-secret-key
   heroku config:set GOOGLE_CLIENT_ID=your-google-client-id
   heroku config:set GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```

2. Add your production URL as an authorized redirect URI in Google Cloud Console

3. For Heroku PostgreSQL, the `DATABASE_URL` is automatically set

4. Verify OAuth consent screen settings are appropriate for public use

## Security Best Practices

1. **Never commit credentials** - Use environment variables
2. **Use HTTPS in production** - Required by Google for OAuth
3. **Rotate secrets regularly** - Update your `SECRET_KEY` and OAuth credentials periodically
4. **Limit redirect URIs** - Only add necessary URLs
5. **Monitor OAuth usage** - Check Google Cloud Console for suspicious activity

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Authlib Documentation](https://docs.authlib.org/)
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
