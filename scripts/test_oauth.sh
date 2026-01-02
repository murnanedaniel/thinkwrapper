#!/bin/bash
# Manual test script for Google OAuth integration

echo "=== ThinkWrapper Google OAuth Manual Test ==="
echo ""

# Check environment variables
echo "1. Checking environment variables..."
if [ -z "$GOOGLE_CLIENT_ID" ]; then
    echo "   ⚠️  GOOGLE_CLIENT_ID is not set"
else
    echo "   ✓ GOOGLE_CLIENT_ID is set"
fi

if [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "   ⚠️  GOOGLE_CLIENT_SECRET is not set"
else
    echo "   ✓ GOOGLE_CLIENT_SECRET is set"
fi

if [ -z "$SECRET_KEY" ]; then
    echo "   ⚠️  SECRET_KEY is not set (will use default for development)"
else
    echo "   ✓ SECRET_KEY is set"
fi

echo ""

# Check if app can start
echo "2. Testing app startup..."
python3 -c "from app import create_app; app = create_app(); print('   ✓ App created successfully')" 2>&1 || echo "   ✗ App creation failed"

echo ""

# Run tests
echo "3. Running authentication tests..."
python3 -m pytest tests/test_auth.py tests/test_auth_integration.py -v --tb=short 2>&1 | grep -E "(PASSED|FAILED|ERROR|test_)"

echo ""

# Check routes
echo "4. Checking OAuth routes are registered..."
python3 << EOF
from app import create_app
app = create_app()
routes = [str(rule) for rule in app.url_map.iter_rules()]
oauth_routes = [r for r in routes if '/api/auth/' in r]
if oauth_routes:
    print("   ✓ OAuth routes found:")
    for route in oauth_routes:
        print(f"     - {route}")
else:
    print("   ✗ No OAuth routes found")
EOF

echo ""
echo "=== Manual Testing Steps ==="
echo ""
echo "To test the OAuth flow manually:"
echo "1. Start the Flask development server:"
echo "   flask --app app run --debug"
echo ""
echo "2. Open http://localhost:5000 in your browser"
echo ""
echo "3. Click 'Login' or 'Sign Up'"
echo ""
echo "4. Click 'Continue with Google'"
echo ""
echo "5. Complete the Google authentication"
echo ""
echo "6. Verify you are redirected back and logged in"
echo ""
echo "7. Check that your name/email appears in the header"
echo ""
echo "8. Click 'Logout' to test the logout flow"
echo ""
echo "For troubleshooting, see GOOGLE_OAUTH_SETUP.md"
echo ""
