"""Tests for Google OAuth authentication."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app import create_app
from app.models import User

@pytest.fixture
def client():
    """Create a test client for the app."""
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_oauth():
    """Mock OAuth client."""
    with patch('app.auth_routes.oauth') as mock:
        yield mock

def test_login_redirects_to_google(client, mock_oauth):
    """Test that login endpoint initiates Google OAuth."""
    mock_oauth.google.authorize_redirect.return_value = 'redirect-response'
    
    response = client.get('/api/auth/login')
    
    # Should call authorize_redirect
    mock_oauth.google.authorize_redirect.assert_called_once()

def test_callback_success(client, mock_oauth):
    """Test successful OAuth callback."""
    # Mock the OAuth token and user info
    mock_token = {
        'userinfo': {
            'sub': 'google-user-123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
    }
    mock_oauth.google.authorize_access_token.return_value = mock_token
    
    with patch('app.auth_routes.db_session') as mock_db_session:
        mock_session = MagicMock()
        mock_db_session.return_value = mock_session
        
        # Mock query to return no existing user
        mock_query = mock_session.query.return_value
        mock_query.filter_by.return_value.first.return_value = None
        
        with patch('app.auth_routes.login_user') as mock_login:
            response = client.get('/api/auth/callback')
            
            # Should create new user and log in
            assert mock_session.add.called
            assert mock_session.commit.called
            assert mock_login.called

def test_callback_existing_user(client, mock_oauth):
    """Test OAuth callback with existing user."""
    mock_token = {
        'userinfo': {
            'sub': 'google-user-123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
    }
    mock_oauth.google.authorize_access_token.return_value = mock_token
    
    with patch('app.auth_routes.db_session') as mock_db_session:
        mock_session = MagicMock()
        mock_db_session.return_value = mock_session
        
        # Mock existing user
        existing_user = User(
            id=1,
            email='test@example.com',
            name='Test User',
            oauth_provider='google',
            oauth_id='google-user-123'
        )
        mock_query = mock_session.query.return_value
        mock_query.filter_by.return_value.first.return_value = existing_user
        
        with patch('app.auth_routes.login_user') as mock_login:
            response = client.get('/api/auth/callback')
            
            # Should not add new user, just log in
            assert not mock_session.add.called
            assert mock_login.called

def test_callback_failure(client, mock_oauth):
    """Test OAuth callback with no user info."""
    mock_oauth.google.authorize_access_token.return_value = {}
    
    response = client.get('/api/auth/callback')
    
    assert response.status_code == 400
    assert b'error' in response.data

def test_get_user_authenticated(client):
    """Test getting authenticated user info."""
    with patch('app.auth_routes.current_user') as mock_user:
        mock_user.is_authenticated = True
        mock_user.email = 'test@example.com'
        mock_user.name = 'Test User'
        mock_user.id = 1
        
        response = client.get('/api/auth/user')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['authenticated'] is True
        assert data['email'] == 'test@example.com'

def test_get_user_not_authenticated(client):
    """Test getting user info when not authenticated."""
    with patch('app.auth_routes.current_user') as mock_user:
        mock_user.is_authenticated = False
        
        response = client.get('/api/auth/user')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['authenticated'] is False

def test_logout(client):
    """Test logout endpoint."""
    # The logout endpoint requires authentication, so it will redirect
    # to the login page or return 401 if not authenticated
    response = client.get('/api/auth/logout')
    
    # Should redirect or return unauthorized since we're not logged in
    assert response.status_code in [302, 401]
