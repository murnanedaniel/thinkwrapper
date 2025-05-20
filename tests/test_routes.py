import pytest
from app import create_app

@pytest.fixture
def client():
    """Create a test client for the app."""
    app = create_app({'TESTING': True})
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_generate_newsletter(client):
    """Test the newsletter generation endpoint."""
    response = client.post('/api/generate', json={
        'topic': 'Artificial Intelligence',
        'name': 'AI Weekly',
        'schedule': 'weekly'
    })
    assert response.status_code == 202
    assert 'status' in response.json
    assert response.json['status'] == 'processing'

def test_generate_newsletter_missing_topic(client):
    """Test the newsletter generation endpoint with missing topic."""
    response = client.post('/api/generate', json={
        'name': 'AI Weekly',
        'schedule': 'weekly'
    })
    assert response.status_code == 400
    assert 'error' in response.json 