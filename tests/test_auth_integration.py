"""Integration test for Google OAuth authentication flow."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app import create_app
from app.models import User

@pytest.fixture
def app():
    """Create test app."""
    test_app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    return test_app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

def test_full_oauth_flow_new_user(client):
    """Test complete OAuth flow for a new user."""
    # Step 1: User clicks login button - should redirect to Google
    with patch('app.auth_routes.oauth') as mock_oauth:
        mock_oauth.google.authorize_redirect.return_value = 'google-auth-url'
        
        response = client.get('/api/auth/login')
        
        # Should initiate OAuth flow
        assert mock_oauth.google.authorize_redirect.called
    
    # Step 2: Google redirects back with auth code - callback endpoint
    with patch('app.auth_routes.oauth') as mock_oauth:
        mock_token = {
            'userinfo': {
                'sub': 'google-123456',
                'email': 'newuser@example.com',
                'name': 'New User'
            }
        }
        mock_oauth.google.authorize_access_token.return_value = mock_token
        
        with patch('app.auth_routes.get_db_session') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # No existing user
            mock_query = mock_db.query.return_value
            mock_query.filter_by.return_value.first.return_value = None
            
            with patch('app.auth_routes.login_user') as mock_login:
                response = client.get('/api/auth/callback')
                
                # Should create new user
                assert mock_db.add.called
                assert mock_db.commit.called
                
                # Should log in the user
                assert mock_login.called
                
                # Should redirect to home
                assert response.status_code == 302

def test_full_oauth_flow_existing_user(client):
    """Test complete OAuth flow for an existing user."""
    # User already exists in database
    with patch('app.auth_routes.oauth') as mock_oauth:
        mock_token = {
            'userinfo': {
                'sub': 'google-123456',
                'email': 'existinguser@example.com',
                'name': 'Existing User'
            }
        }
        mock_oauth.google.authorize_access_token.return_value = mock_token
        
        with patch('app.auth_routes.get_db_session') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Return existing user
            existing_user = User(
                id=1,
                email='existinguser@example.com',
                name='Existing User',
                oauth_provider='google',
                oauth_id='google-123456'
            )
            mock_query = mock_db.query.return_value
            mock_query.filter_by.return_value.first.return_value = existing_user
            
            with patch('app.auth_routes.login_user') as mock_login:
                response = client.get('/api/auth/callback')
                
                # Should NOT create new user
                assert not mock_db.add.called
                
                # Should log in the existing user
                assert mock_login.called
                mock_login.assert_called_once_with(existing_user)
                
                # Should redirect to home
                assert response.status_code == 302

def test_oauth_failure_no_user_info(client):
    """Test OAuth callback when Google doesn't return user info."""
    with patch('app.auth_routes.oauth') as mock_oauth:
        # Return token without userinfo
        mock_oauth.google.authorize_access_token.return_value = {}
        
        response = client.get('/api/auth/callback')
        
        # Should return error
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

def test_oauth_failure_exception(client):
    """Test OAuth callback when an exception occurs."""
    with patch('app.auth_routes.oauth') as mock_oauth:
        # Simulate an exception during token exchange
        mock_oauth.google.authorize_access_token.side_effect = Exception('OAuth error')
        
        response = client.get('/api/auth/callback')
        
        # Should return error
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

def test_login_logout_cycle(client):
    """Test full login and logout cycle."""
    # Login
    with patch('app.auth_routes.oauth') as mock_oauth:
        mock_token = {
            'userinfo': {
                'sub': 'google-789',
                'email': 'testuser@example.com',
                'name': 'Test User'
            }
        }
        mock_oauth.google.authorize_access_token.return_value = mock_token
        
        with patch('app.auth_routes.get_db_session') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            user = User(
                id=1,
                email='testuser@example.com',
                name='Test User',
                oauth_provider='google',
                oauth_id='google-789'
            )
            mock_query = mock_db.query.return_value
            mock_query.filter_by.return_value.first.return_value = user
            
            with patch('app.auth_routes.login_user'):
                response = client.get('/api/auth/callback')
                assert response.status_code == 302
    
    # Logout (without authentication for simplicity in test)
    response = client.get('/api/auth/logout')
    
    # Should redirect or require authentication
    assert response.status_code in [302, 401]
