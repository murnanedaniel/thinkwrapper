import pytest
from unittest.mock import patch, Mock
from app import create_app


@pytest.fixture
def client():
    """Create a test client for the app."""
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


@patch('app.routes.generate_newsletter_async')
def test_generate_newsletter(mock_task, client):
    """Test the newsletter generation endpoint."""
    # Mock the Celery task
    mock_result = Mock()
    mock_result.id = 'test-task-id-123'
    mock_task.delay.return_value = mock_result

    response = client.post('/api/generate', json={
        'topic': 'Artificial Intelligence',
        'style': 'concise'
    })
    assert response.status_code == 202
    assert response.json['success'] is True
    assert response.json['status'] == 'processing'
    assert response.json['task_id'] == 'test-task-id-123'

    # Verify task was called
    mock_task.delay.assert_called_once_with('Artificial Intelligence', 'concise')


@patch('app.routes.generate_newsletter_async')
def test_generate_newsletter_default_style(mock_task, client):
    """Test newsletter generation with default style."""
    mock_result = Mock()
    mock_result.id = 'test-task-id-456'
    mock_task.delay.return_value = mock_result

    response = client.post('/api/generate', json={
        'topic': 'AI News'
    })
    assert response.status_code == 202
    assert response.json['success'] is True
    assert response.json['task_id'] == 'test-task-id-456'

    # Verify task was called with default style
    mock_task.delay.assert_called_once_with('AI News', 'concise')


def test_generate_newsletter_missing_topic(client):
    """Test the newsletter generation endpoint with missing topic."""
    response = client.post('/api/generate', json={
        'style': 'concise'
    })
    assert response.status_code == 400
    assert 'error' in response.json


@patch('app.celery_config.celery.AsyncResult')
def test_get_task_status_pending(mock_async_result, client):
    """Test getting status of a pending task."""
    mock_task = Mock()
    mock_task.state = 'PENDING'
    mock_async_result.return_value = mock_task

    response = client.get('/api/task/test-task-id')
    assert response.status_code == 200
    assert response.json['state'] == 'PENDING'
    assert 'status' in response.json


@patch('app.celery_config.celery.AsyncResult')
def test_get_task_status_success(mock_async_result, client):
    """Test getting status of a successful task."""
    mock_task = Mock()
    mock_task.state = 'SUCCESS'
    mock_task.result = {'subject': 'Test Subject', 'content': 'Test Content'}
    mock_async_result.return_value = mock_task

    response = client.get('/api/task/test-task-id')
    assert response.status_code == 200
    assert response.json['state'] == 'SUCCESS'
    assert response.json['result']['subject'] == 'Test Subject'


@patch('app.celery_config.celery.AsyncResult')
def test_get_task_status_failure(mock_async_result, client):
    """Test getting status of a failed task."""
    mock_task = Mock()
    mock_task.state = 'FAILURE'
    mock_task.info = Exception('Task failed')
    mock_async_result.return_value = mock_task

    response = client.get('/api/task/test-task-id')
    assert response.status_code == 200
    assert response.json['state'] == 'FAILURE'
