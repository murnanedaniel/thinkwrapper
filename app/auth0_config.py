import os

# Auth0 Configuration
AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN', 'dev-26w2jl00f1tc85cq.us.auth0.com')
AUTH0_CLIENT_ID = os.environ.get('AUTH0_CLIENT_ID', 'Wo2xo4VE3fHctnAzRm1U6WIzXtNkgyUY')
AUTH0_CLIENT_SECRET = os.environ.get('AUTH0_CLIENT_SECRET', 'YCbb7vmHqR7a_1Af-SbJ3A06EvIcGtuSpIOH1oiAcPPRf3fs058HGurr1U6bQano')

# API audience - set this if you have APIs in Auth0
# AUTH0_API_AUDIENCE = os.environ.get('AUTH0_API_AUDIENCE', 'your-api-identifier')

# Callback URL - must match what's configured in Auth0
AUTH0_CALLBACK_URL = os.environ.get('AUTH0_CALLBACK_URL', 'https://thinkwrapper-app-80e87f9b5892.herokuapp.com/auth/callback')

# Logout URL - must match what's configured in Auth0
AUTH0_LOGOUT_URL = os.environ.get('AUTH0_LOGOUT_URL', 'https://thinkwrapper-app-80e87f9b5892.herokuapp.com') 