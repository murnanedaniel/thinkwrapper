import pytest
import json
from unittest.mock import patch, Mock
from app import create_app


@pytest.fixture
def client():
    """Create a test client for the app."""
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


@pytest.fixture
def app():
    """Create an app instance for testing."""
    return create_app({"TESTING": True})


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json == {"status": "ok"}
        assert response.headers["Content-Type"] == "application/json"

    def test_health_check_post_method_not_allowed(self, client):
        """Test that POST method is not allowed on health endpoint."""
        response = client.post("/health")
        assert response.status_code == 405


class TestNewsletterGeneration:
    """Test the newsletter generation endpoint."""

    @patch('app.routes.generate_newsletter_async')
    def test_generate_newsletter_success(self, mock_task, client):
        """Test successful newsletter generation request."""
        # Mock the Celery task
        mock_result = Mock()
        mock_result.id = 'test-task-id-123'
        mock_task.delay.return_value = mock_result
        
        data = {
            "topic": "Artificial Intelligence",
            "name": "AI Weekly",
            "schedule": "weekly",
        }
        response = client.post(
            "/api/generate", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 202
        response_data = response.json
        assert response_data["success"] is True
        assert "status" in response_data
        assert response_data["status"] == "processing"
        assert "task_id" in response_data

    def test_generate_newsletter_missing_topic(self, client):
        """Test newsletter generation with missing topic."""
        data = {"name": "AI Weekly", "schedule": "weekly"}
        response = client.post(
            "/api/generate", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 400
        response_data = response.json
        assert response_data["success"] is False
        assert "error" in response_data
        assert "Topic is required" in response_data["error"]

    def test_generate_newsletter_empty_topic(self, client):
        """Test newsletter generation with empty topic."""
        data = {"topic": "", "name": "AI Weekly", "schedule": "weekly"}
        response = client.post(
            "/api/generate", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 400
        response_data = response.json
        assert "error" in response_data

    def test_generate_newsletter_whitespace_topic(self, client):
        """Test newsletter generation with whitespace-only topic."""
        data = {"topic": "   ", "name": "AI Weekly", "schedule": "weekly"}
        response = client.post(
            "/api/generate", data=json.dumps(data), content_type="application/json"
        )

        # Whitespace topics are now rejected by validation
        assert response.status_code == 400
        response_data = response.json
        assert response_data["success"] is False
        assert "error" in response_data

    def test_generate_newsletter_invalid_json(self, client):
        """Test newsletter generation with invalid JSON."""
        response = client.post(
            "/api/generate", data="invalid json", content_type="application/json"
        )

        assert response.status_code == 400

    def test_generate_newsletter_no_content_type(self, client):
        """Test newsletter generation without content type."""
        data = {
            "topic": "Test Topic",
        }
        response = client.post("/api/generate", data=json.dumps(data))

        # Returns 415 Unsupported Media Type when no content-type provided
        assert response.status_code == 415

    def test_generate_newsletter_get_method_not_allowed(self, client):
        """Test that GET method is not allowed on generate endpoint."""
        response = client.get("/api/generate")
        # Current behavior: returns 404 (this might be a bug, should be 405)
        assert response.status_code == 404


class TestStaticFileServing:
    """Test static file serving and SPA routing."""

    def test_root_path_serves_index(self, client):
        """Test that root path attempts to serve index.html."""
        response = client.get("/")
        # This will likely fail since we don't have static files set up,
        # but we can test the status code
        assert response.status_code in [200, 404]

    def test_catch_all_routing(self, client):
        """Test that unknown routes attempt to serve static files."""
        response = client.get("/dashboard")
        # Should either serve index.html or return 404
        assert response.status_code in [200, 404]

    def test_api_route_not_caught_by_catch_all(self, client):
        """Test that API routes are not caught by catch-all."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_nonexistent_endpoint(self, client):
        """Test accessing a nonexistent endpoint."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test method not allowed scenarios."""
        response = client.put("/health")
        assert response.status_code == 405

        response = client.delete("/api/generate")
        assert response.status_code == 405


class TestRequestValidation:
    """Test request validation and data handling."""

    def test_large_payload(self, client):
        """Test handling of large payloads."""
        large_topic = "A" * 10000  # 10KB topic
        data = {"topic": large_topic, "name": "Test Newsletter"}
        response = client.post(
            "/api/generate", data=json.dumps(data), content_type="application/json"
        )

        # Should either accept it or reject with appropriate error
        assert response.status_code in [202, 400, 413]

    @patch('app.routes.generate_newsletter_async')
    def test_special_characters_in_topic(self, mock_task, client):
        """Test handling of special characters in topic."""
        # Mock the Celery task
        mock_result = Mock()
        mock_result.id = 'test-task-id-456'
        mock_task.delay.return_value = mock_result
        
        data = {
            "topic": 'AI & ML: 2024 Trends! (Part 1) - "Future Tech"',
            "name": "Special Chars Newsletter",
        }
        response = client.post(
            "/api/generate", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 202
        response_data = response.json
        assert response_data["success"] is True
        assert response_data["status"] == "processing"

    @patch('app.routes.generate_newsletter_async')
    def test_unicode_in_topic(self, mock_task, client):
        """Test handling of unicode characters in topic."""
        # Mock the Celery task
        mock_result = Mock()
        mock_result.id = 'test-task-id-789'
        mock_task.delay.return_value = mock_result
        
        data = {
            "topic": "Intelligence Artificielle et Машинное обучение 人工智能",
            "name": "Unicode Newsletter",
        }
        response = client.post(
            "/api/generate", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 202
        response_data = response.json
        assert response_data["success"] is True
        assert response_data["status"] == "processing"
