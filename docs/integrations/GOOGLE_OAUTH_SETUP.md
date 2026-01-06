# Google OAuth Setup Guide

This comprehensive guide will walk you through setting up Google OAuth authentication for ThinkWrapper, from creating a Google Cloud project to obtaining your Client ID and Client Secret.

## Prerequisites

- A Google account (free)
- ThinkWrapper application code downloaded/cloned
- Basic familiarity with environment variables

**Time to Complete:** Approximately 10-15 minutes

---

## Step 1: Create a Google Cloud Project

### 1.1 Access Google Cloud Console

1. Navigate to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account if prompted
3. If this is your first time, you may need to accept the Terms of Service

### 1.2 Create a New Project

1. At the top of the page, click the **project dropdown** (it may say "Select a project" or show your current project name)
2. In the dialog that appears, click **"NEW PROJECT"** in the top-right corner
3. Fill in the project details:
   - **Project name**: Enter a descriptive name (e.g., `ThinkWrapper-OAuth` or `ThinkWrapper-Dev`)
   - **Organization**: Leave as "No organization" if you're not part of one
   - **Location**: Leave as default or select your organization
4. Click **"CREATE"**
5. Wait a few seconds for the project to be created
6. You'll receive a notification when it's ready - click **"SELECT PROJECT"** or use the project dropdown to switch to your new project

**Note:** The Project ID (shown below the project name) will be auto-generated. You don't need this for OAuth setup.

---

## Step 2: Configure OAuth Consent Screen

**Important:** You must configure the consent screen *before* creating OAuth credentials. This is the screen users see when they authenticate with Google.

### 2.1 Navigate to OAuth Consent Screen

1. From the Google Cloud Console, open the **navigation menu** (☰ hamburger icon in top-left)
2. Navigate to: **APIs & Services** → **OAuth consent screen**
3. You should see the "OAuth consent screen" configuration page

### 2.2 Choose User Type

1. Select **"External"** as the User Type
   - This allows anyone with a Google account to authenticate
   - "Internal" is only available for Google Workspace organizations
2. Click **"CREATE"**

### 2.3 Configure App Information

On the "OAuth consent screen" page, fill in the required fields:

1. **App name**: `ThinkWrapper` (or your preferred name - this is shown to users)
2. **User support email**: Select your email from the dropdown
3. **App logo**: (Optional) Upload a logo if you have one
4. **Application home page**: (Optional) e.g., `http://localhost:5000` for development
5. **Application privacy policy link**: (Optional) Can leave blank for development
6. **Application terms of service link**: (Optional) Can leave blank for development
7. **Authorized domains**: (Leave empty for local development)
8. **Developer contact information**: Enter your email address

Click **"SAVE AND CONTINUE"**

### 2.4 Configure Scopes

1. On the "Scopes" page, you can click **"ADD OR REMOVE SCOPES"** if you want to review
2. For basic OAuth, the default scopes are sufficient:
   - `openid`
   - `email`
   - `profile`
3. These are automatically included by the OAuth library
4. Click **"SAVE AND CONTINUE"**

### 2.5 Add Test Users (Development Only)

1. On the "Test users" page, click **"ADD USERS"**
2. Enter the email addresses of Google accounts you want to test with (including your own)
3. Click **"ADD"**
4. Click **"SAVE AND CONTINUE"**

**Note:** While your app is in "Testing" status, only test users can authenticate. To make it public, you'll need to submit for verification later.

### 2.6 Review Summary

1. Review the summary page
2. Click **"BACK TO DASHBOARD"**

---

## Step 3: Enable Required APIs

### 3.1 Navigate to API Library

1. From the navigation menu (☰), go to: **APIs & Services** → **Library**
2. You'll see the API Library with searchable API services

### 3.2 Enable Google Identity Services

1. In the search bar, type: `Google Identity`
2. Look for **"Google Identity Toolkit API"** or similar identity service
3. Click on it
4. Click **"ENABLE"**
5. Wait a few seconds for it to activate

**Alternative:** The newer approach uses OpenID Connect which doesn't require enabling specific APIs beyond the OAuth consent configuration. The ThinkWrapper code uses the standard OpenID Connect discovery endpoint, so you may not need to enable additional APIs.

---

## Step 4: Create OAuth 2.0 Credentials

This is where you'll get your **Client ID** and **Client Secret**.

### 4.1 Navigate to Credentials

1. From the navigation menu (☰), go to: **APIs & Services** → **Credentials**
2. You should see the "Credentials" page with options to create various credential types

### 4.2 Create OAuth Client ID

1. Click **"+ CREATE CREDENTIALS"** at the top
2. Select **"OAuth client ID"** from the dropdown
3. If prompted to configure the consent screen and you haven't done Step 2, go back and complete it

### 4.3 Configure Application Type

1. **Application type**: Select **"Web application"**
2. **Name**: Enter a descriptive name (e.g., `ThinkWrapper Web Client` or `ThinkWrapper Local Dev`)

### 4.4 Set Authorized Redirect URIs

This is **critical** - the redirect URI must exactly match what your application uses.

1. Under **"Authorized redirect URIs"**, click **"+ ADD URI"**
2. For **local development**, add:
   ```
   http://localhost:5000/api/auth/callback
   ```
3. For **production deployment**, add your production URL:
   ```
   https://your-domain.com/api/auth/callback
   ```
   Replace `your-domain.com` with your actual domain

**Important Notes:**
- No trailing slash
- Exact protocol match (http vs https)
- Exact port match (if using a non-standard port)
- Must match the callback route in `app/auth_routes.py`

4. You can add multiple URIs for different environments (dev, staging, prod)

### 4.5 Create and Save Credentials

1. Click **"CREATE"**
2. A dialog will appear showing your **Client ID** and **Client Secret**
3. **IMPORTANT:** Copy both values immediately:
   - **Your Client ID**: A long string ending in `.apps.googleusercontent.com`
   - **Your Client Secret**: A shorter secret string
4. Click **"OK"**

**Security Note:** Your Client Secret is sensitive. Treat it like a password. If exposed, you can regenerate it from the Credentials page.

### 4.6 Access Credentials Later

1. On the "Credentials" page, you'll see your OAuth 2.0 Client ID listed
2. Click on it to view details
3. You can see your Client ID anytime
4. To view or reset your Client Secret, look in the client details

---

## Step 5: Configure Environment Variables in ThinkWrapper

Now that you have your credentials, you need to configure ThinkWrapper to use them.

### 5.1 Locate the .env.example File

1. In your ThinkWrapper project directory, find the `.env.example` file
2. This file contains template environment variables

### 5.2 Create Your .env File

1. **Copy** `.env.example` to create a new `.env` file:
   ```bash
   cp .env.example .env
   ```
2. **IMPORTANT:** The `.env` file is in `.gitignore` and should NEVER be committed to git

### 5.3 Add Your Google OAuth Credentials

Open the `.env` file in a text editor and update these variables:

```bash
# Google OAuth Credentials from Step 4
GOOGLE_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-actual-client-secret

# Generate a secure random secret key for Flask sessions
SECRET_KEY=your-long-random-secret-key-here
```

**To generate a secure SECRET_KEY**, run in terminal:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5.4 Complete Other Required Variables

Make sure these are also set in your `.env` file:

```bash
# Flask Configuration
FLASK_ENV=development

# Database (for local development)
DATABASE_URL=postgresql://localhost:5432/thinkwrapper
# Or use SQLite for simplicity:
# DATABASE_URL=sqlite:///thinkwrapper.db

# Other API keys can be left as placeholders for now
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
```

---

## Step 6: Test the OAuth Integration

Now you're ready to test the complete OAuth flow!

### 6.1 Install Dependencies

If you haven't already:
```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 6.2 Start the Flask Application

```bash
flask --app app run --debug
```

You should see output like:
```
 * Running on http://127.0.0.1:5000
```

### 6.3 Test the Login Flow

1. Open your browser and navigate to:
   ```
   http://localhost:5000/api/auth/login
   ```

2. You should be **redirected to Google's login page**
   - If you see a Google sign-in page, the redirect is working! ✅

3. **Sign in** with a Google account (must be a test user if app is in Testing mode)

4. **Grant permissions** when prompted
   - Google will ask to share your email and basic profile
   - Click "Continue" or "Allow"

5. You should be **redirected back** to your ThinkWrapper app
   - Default redirect is to `http://localhost:5000/`
   - Check the browser URL and network tab

### 6.4 Verify User Authentication

Check if the user was created and logged in:

```bash
# In a new terminal, check the user endpoint
curl http://localhost:5000/api/auth/user
```

You should see a JSON response with your user information:
```json
{
  "authenticated": true,
  "email": "your-email@gmail.com",
  "name": "Your Name",
  "id": 1
}
```

### 6.5 Test Logout

```bash
# Visit the logout endpoint
curl http://localhost:5000/api/auth/logout
```

---

## Step 7: Verify Database User Creation

### 7.1 Check the Database

If using SQLite (default):
```bash
sqlite3 thinkwrapper.db
sqlite> SELECT * FROM users;
sqlite> .quit
```

If using PostgreSQL:
```bash
psql thinkwrapper
SELECT * FROM users;
\q
```

You should see your user record with:
- `email`: Your Google email
- `name`: Your Google name
- `oauth_provider`: 'google'
- `oauth_id`: Your Google user ID

---

## Troubleshooting Common Issues

### Issue 1: "redirect_uri_mismatch" Error

**Symptom:** Google shows an error page saying the redirect URI doesn't match.

**Cause:** The redirect URI in your Google Cloud Console doesn't match what your app is sending.

**Solutions:**
1. Check the error message for the exact redirect URI that was sent
2. Go to Google Cloud Console → Credentials → Your OAuth Client
3. Verify the redirect URI **exactly matches** (including protocol, port, and path):
   ```
   http://localhost:5000/api/auth/callback
   ```
4. Common mistakes:
   - Using `https` instead of `http` for localhost
   - Adding a trailing slash: `...callback/` ❌
   - Wrong port number
   - Typo in the path
5. Click "SAVE" after making changes
6. Wait 1-2 minutes for changes to propagate
7. Try the login flow again

### Issue 2: "Invalid client" or "Unauthorized client" Error

**Symptom:** Error during OAuth flow about invalid credentials.

**Cause:** Client ID or Client Secret is incorrect or not set.

**Solutions:**
1. Open your `.env` file
2. Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set
3. Check for common issues:
   - Extra spaces before or after the values
   - Missing quotes (values should be plain, not quoted)
   - Copied only part of the credential
4. Go to Google Cloud Console → Credentials
5. Find your OAuth client and verify the Client ID matches
6. If needed, reset the Client Secret and copy the new value
7. Restart your Flask application after changing `.env`

### Issue 3: "Access blocked: This app is not verified"

**Symptom:** Google shows a warning that the app isn't verified.

**Cause:** Your app is in "Testing" mode and the user isn't added as a test user.

**Solutions:**

**Option A - Add Test Users (Quick Fix):**
1. Go to Google Cloud Console → APIs & Services → OAuth consent screen
2. Scroll to "Test users"
3. Click "ADD USERS"
4. Add the Google email addresses that need access
5. Click "SAVE"

**Option B - Proceed Anyway (Testing):**
1. On the warning screen, click "Advanced"
2. Click "Go to [App Name] (unsafe)"
3. This only works for your own apps during development

**Option C - Publish App (For Production):**
1. Complete the OAuth consent screen fully
2. Submit for verification (required for public apps)
3. Verification can take several days

### Issue 4: "Session not persisting" - User Logged Out Immediately

**Symptom:** After successful login, user appears logged out on next request.

**Cause:** `SECRET_KEY` is not set or is changing between requests.

**Solutions:**
1. Verify `SECRET_KEY` is set in your `.env` file
2. Ensure it's a long, random string (at least 32 characters)
3. Generate a proper secret key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
4. Never use simple values like `"test"` or `"secret"` in production
5. Restart Flask after changing `SECRET_KEY`
6. Check Flask is loading the `.env` file (add debug print if needed)

### Issue 5: "Failed to get user info" Error

**Symptom:** Callback succeeds but app shows error about getting user info.

**Cause:** Token doesn't contain user information or API scopes issue.

**Solutions:**
1. Verify scopes in `app/auth.py` include: `'openid email profile'`
2. Check the OAuth consent screen has appropriate scopes
3. Try clearing browser cookies and logging in again
4. Regenerate credentials if problem persists

### Issue 6: Database Connection Errors

**Symptom:** OAuth flow works but user creation fails with database errors.

**Cause:** Database not set up or connection string incorrect.

**Solutions:**
1. For SQLite (simplest):
   ```bash
   # In .env
   DATABASE_URL=sqlite:///thinkwrapper.db
   ```
   The database file will be created automatically

2. For PostgreSQL:
   ```bash
   # Create database
   createdb thinkwrapper
   
   # In .env
   DATABASE_URL=postgresql://localhost:5432/thinkwrapper
   ```

3. Verify database tables exist (they're created automatically on first run)

### Issue 7: "No module named 'authlib'" or Import Errors

**Symptom:** Application won't start, shows import errors.

**Cause:** Dependencies not installed.

**Solutions:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install/reinstall requirements
pip install -r requirements.txt

# Verify authlib is installed
pip list | grep authlib
```

### Issue 8: Working Locally but Broken in Production

**Symptom:** OAuth works on localhost but fails when deployed.

**Cause:** Production redirect URI not configured.

**Solutions:**
1. Go to Google Cloud Console → Credentials → Your OAuth Client
2. Add your production URL to Authorized redirect URIs:
   ```
   https://your-app.herokuapp.com/api/auth/callback
   ```
   (Replace with your actual domain)
3. Ensure production environment has:
   - `GOOGLE_CLIENT_ID` set
   - `GOOGLE_CLIENT_SECRET` set
   - `SECRET_KEY` set (use a different value than dev)
4. For Heroku:
   ```bash
   heroku config:set GOOGLE_CLIENT_ID=your-client-id
   heroku config:set GOOGLE_CLIENT_SECRET=your-client-secret
   heroku config:set SECRET_KEY=your-production-secret
   ```
5. Verify your app uses HTTPS in production (required by Google)

---

## Production Deployment Checklist

When deploying to production (e.g., Heroku, AWS, Google Cloud):

### Pre-Deployment

- [ ] Create a separate OAuth client for production (recommended)
- [ ] Set up production environment variables
- [ ] Verify production domain/URL is decided
- [ ] Ensure production will use HTTPS (required by Google)

### Configure Google Cloud Console

1. **Add Production Redirect URI**
   - Go to: APIs & Services → Credentials → Your OAuth Client
   - Add: `https://your-production-domain.com/api/auth/callback`
   - Click "SAVE"

2. **Consider OAuth Consent Screen Status**
   - "Testing" mode: Only test users can authenticate
   - "In Production" mode: Anyone can authenticate
   - For public apps, submit for verification

### Set Production Environment Variables

For **Heroku**:
```bash
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set GOOGLE_CLIENT_ID=your-production-client-id
heroku config:set GOOGLE_CLIENT_SECRET=your-production-client-secret
heroku config:set FLASK_ENV=production
```

For **AWS/Other Platforms**:
- Use your platform's secret management (e.g., AWS Secrets Manager)
- Or set environment variables through platform console
- Never hardcode credentials in your application code

### Verify Production Setup

After deployment:

1. Visit your login URL: `https://your-domain.com/api/auth/login`
2. Complete OAuth flow
3. Check user endpoint: `https://your-domain.com/api/auth/user`
4. Test logout: `https://your-domain.com/api/auth/logout`

### Monitoring

- Check Google Cloud Console → APIs & Services → Dashboard for OAuth usage
- Monitor application logs for OAuth errors
- Set up alerts for authentication failures

---

## Security Best Practices

### Credential Management

1. **Never commit credentials to git**
   - Always use `.env` files (in `.gitignore`)
   - Use environment variables in production
   - Double-check before committing: `git status`

2. **Use strong SECRET_KEY values**
   - Minimum 32 characters
   - Use `secrets.token_hex(32)` to generate
   - Different key for each environment
   - Rotate periodically (requires user re-login)

3. **Secure GOOGLE_CLIENT_SECRET**
   - Treat like a password
   - Don't share in emails or chat
   - Don't log or display in error messages
   - Rotate if compromised

### Application Security

4. **Always use HTTPS in production**
   - Google requires HTTPS for OAuth
   - Protects token exchange
   - Use services like Let's Encrypt for free SSL

5. **Limit redirect URIs**
   - Only add URIs you actually use
   - Remove old/unused URIs
   - Be specific (don't use wildcards)

6. **Validate user data**
   - Even though it comes from Google
   - Check email format
   - Sanitize names before displaying

7. **Implement session timeout**
   - Consider adding session expiry
   - Force re-authentication for sensitive operations
   - Clear sessions on logout

### OAuth Console Security

8. **Regularly review OAuth consent screen**
   - Keep contact info updated
   - Review scopes (only request what you need)
   - Update app description

9. **Monitor OAuth usage**
   - Check for unusual patterns
   - Review user counts
   - Watch for error spikes

10. **Set up billing alerts**
    - Google Cloud has free tiers
    - Set alerts to avoid surprise charges
    - OAuth itself is free but other APIs may have costs

---

## Advanced Configuration

### Using Multiple Environments

You can create separate OAuth clients for different environments:

**Development:**
- OAuth Client: "ThinkWrapper Dev"
- Redirect URI: `http://localhost:5000/api/auth/callback`
- Scopes: All needed scopes

**Staging:**
- OAuth Client: "ThinkWrapper Staging"  
- Redirect URI: `https://staging.yourdomain.com/api/auth/callback`
- Scopes: Same as production

**Production:**
- OAuth Client: "ThinkWrapper Production"
- Redirect URI: `https://www.yourdomain.com/api/auth/callback`
- Scopes: Minimal necessary scopes

Benefits:
- Isolate credentials
- Track usage per environment
- Revoke without affecting others

### Custom Scopes

To request additional Google user data, modify `app/auth.py`:

```python
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile https://www.googleapis.com/auth/calendar.readonly'
    }
)
```

Then update OAuth consent screen to request the additional scopes.

### Publishing Your App

To allow any Google user to authenticate:

1. Complete all fields in OAuth consent screen
2. Add privacy policy and terms of service URLs
3. Submit for verification:
   - Go to OAuth consent screen
   - Click "PUBLISH APP"
   - Fill out verification questionnaire
4. Verification process takes 1-6 weeks
5. You'll receive email when approved

---

## Quick Reference

### Important URLs

| Resource | URL |
|----------|-----|
| Google Cloud Console | https://console.cloud.google.com/ |
| OAuth 2.0 Playground (Testing) | https://developers.google.com/oauthplayground/ |
| Google OAuth Docs | https://developers.google.com/identity/protocols/oauth2 |
| Authlib Docs | https://docs.authlib.org/ |

### Key Files in ThinkWrapper

| File | Purpose |
|------|---------|
| `app/auth.py` | OAuth configuration and initialization |
| `app/auth_routes.py` | Login, callback, logout endpoints |
| `app/models.py` | User model with OAuth fields |
| `.env` | Environment variables (not in git) |
| `.env.example` | Template for environment variables |

### Environment Variables Quick Reference

```bash
# Required for OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
SECRET_KEY=your-long-random-secret

# Required for app
FLASK_ENV=development
DATABASE_URL=sqlite:///thinkwrapper.db

# Optional but recommended
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Testing Checklist

- [ ] Login redirects to Google
- [ ] Can sign in with test user
- [ ] Redirected back to app after auth
- [ ] User info accessible at `/api/auth/user`
- [ ] User record created in database
- [ ] Logout works and clears session
- [ ] Can log in again after logout
- [ ] Error handling works (try invalid client ID)

---

## Getting Help

### Common Commands

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Test OAuth endpoint
curl http://localhost:5000/api/auth/user

# Check database (SQLite)
sqlite3 thinkwrapper.db "SELECT * FROM users;"

# Check environment variables are loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GOOGLE_CLIENT_ID'))"

# Run auth tests
pytest tests/test_auth.py tests/test_auth_integration.py -v
```

### Support Resources

- **ThinkWrapper Issues**: Report bugs or ask questions in GitHub Issues
- **Google OAuth Support**: https://support.google.com/cloud/
- **Authlib Documentation**: https://docs.authlib.org/en/latest/
- **Flask-Login Documentation**: https://flask-login.readthedocs.io/

### Debugging Tips

1. **Enable Flask debug mode**: Set `FLASK_ENV=development`
2. **Check Flask logs**: Look for error messages in console
3. **Use browser DevTools**: Check Network tab for failed requests
4. **Test with curl**: Isolate frontend vs backend issues
5. **Verify .env loading**: Print environment variables to confirm
6. **Try OAuth Playground**: Test credentials independently

---

## Summary

You should now have:
- ✅ Google Cloud project created
- ✅ OAuth consent screen configured  
- ✅ OAuth client credentials generated
- ✅ Client ID and Client Secret obtained
- ✅ ThinkWrapper configured with credentials
- ✅ Tested the complete OAuth flow
- ✅ User authentication working

**Next Steps:**
- Set up other API keys (OpenAI, Anthropic) for full functionality
- Deploy to production when ready
- Submit for OAuth verification if making app public

---

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [OpenID Connect Documentation](https://openid.net/connect/)
- [Authlib Documentation](https://docs.authlib.org/)
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)

---

*Last Updated: January 2026*
