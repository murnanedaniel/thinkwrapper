import pytest
import os
from unittest.mock import patch, Mock
from app import services, create_app


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = create_app({"TESTING": True})
    return app


@pytest.fixture
def app_context(app):
    """Create an application context for tests."""
    with app.app_context():
        yield app


class TestBraveSearchAPI:
    """Test Brave Search API integration."""

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_search_brave_success(self, mock_get, app_context):
        """Test successful Brave Search API call."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "Test Result 1",
                        "url": "https://example.com/1",
                        "description": "Description 1",
                    },
                    {
                        "title": "Test Result 2",
                        "url": "https://example.com/2",
                        "description": "Description 2",
                    },
                ]
            }
        }
        mock_get.return_value = mock_response

        result = services.search_brave("test query", count=10)

        assert result["success"] is True
        assert result["source"] == "brave"
        assert result["query"] == "test query"
        assert len(result["results"]) == 2
        assert result["total_results"] == 2
        assert result["results"][0]["title"] == "Test Result 1"
        assert result["results"][0]["url"] == "https://example.com/1"
        assert result["results"][0]["description"] == "Description 1"

        # Verify API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://api.search.brave.com/res/v1/web/search" in call_args[0]
        assert call_args[1]["params"]["q"] == "test query"
        assert call_args[1]["params"]["count"] == 10
        assert call_args[1]["headers"]["X-Subscription-Token"] == "test-api-key"

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_search_brave_with_different_count(self, mock_get, app_context):
        """Test Brave Search with custom result count."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": f"Result {i}",
                        "url": f"https://example.com/{i}",
                        "description": f"Desc {i}",
                    }
                    for i in range(5)
                ]
            }
        }
        mock_get.return_value = mock_response

        result = services.search_brave("python tutorial", count=5)

        assert result["success"] is True
        assert len(result["results"]) == 5
        assert mock_get.call_args[1]["params"]["count"] == 5

    @patch.dict(os.environ, {}, clear=True)
    def test_search_brave_no_api_key_with_fallback(self, app_context):
        """Test Brave Search without API key falls back to mock."""
        result = services.search_brave("test query", count=3, fallback_to_mock=True)

        assert result["success"] is True
        assert result["source"] == "mock"
        assert result["query"] == "test query"
        assert len(result["results"]) == 3
        assert "Mock Result 1" in result["results"][0]["title"]

    @patch.dict(os.environ, {}, clear=True)
    def test_search_brave_no_api_key_without_fallback(self, app_context):
        """Test Brave Search without API key and no fallback."""
        result = services.search_brave("test query", fallback_to_mock=False)

        assert result["success"] is False
        assert result["source"] == "brave"
        assert result["query"] == "test query"
        assert len(result["results"]) == 0
        assert "API key not configured" in result["error"]

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_search_brave_api_error_with_fallback(self, mock_get, app_context):
        """Test Brave Search handles API errors with fallback."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = services.search_brave("test query", fallback_to_mock=True)

        assert result["success"] is True
        assert result["source"] == "mock"
        assert len(result["results"]) > 0

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_search_brave_api_error_without_fallback(self, mock_get, app_context):
        """Test Brave Search handles API errors without fallback."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = services.search_brave("test query", fallback_to_mock=False)

        assert result["success"] is False
        assert result["source"] == "brave"
        assert "status code 500" in result["error"]
        assert len(result["results"]) == 0

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_search_brave_timeout_with_fallback(self, mock_get, app_context):
        """Test Brave Search handles timeout with fallback."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        result = services.search_brave("test query", fallback_to_mock=True)

        assert result["success"] is True
        assert result["source"] == "mock"
        assert len(result["results"]) > 0

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_search_brave_timeout_without_fallback(self, mock_get, app_context):
        """Test Brave Search handles timeout without fallback."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        result = services.search_brave("test query", fallback_to_mock=False)

        assert result["success"] is False
        assert "timed out" in result["error"]
        assert len(result["results"]) == 0

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_search_brave_generic_exception_with_fallback(self, mock_get, app_context):
        """Test Brave Search handles generic exceptions with fallback."""
        mock_get.side_effect = Exception("Network error")

        result = services.search_brave("test query", fallback_to_mock=True)

        assert result["success"] is True
        assert result["source"] == "mock"
        assert len(result["results"]) > 0

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_search_brave_generic_exception_without_fallback(
        self, mock_get, app_context
    ):
        """Test Brave Search handles generic exceptions without fallback."""
        mock_get.side_effect = Exception("Network error")

        result = services.search_brave("test query", fallback_to_mock=False)

        assert result["success"] is False
        assert "Network error" in result["error"]
        assert len(result["results"]) == 0


class TestBraveSearchResultsParsing:
    """Test parsing of Brave Search API results."""

    def test_parse_brave_results_standard_format(self):
        """Test parsing standard Brave API response."""
        data = {
            "web": {
                "results": [
                    {
                        "title": "Python Documentation",
                        "url": "https://python.org/docs",
                        "description": "Official Python documentation",
                    },
                    {
                        "title": "Python Tutorial",
                        "url": "https://python.org/tutorial",
                        "description": "Learn Python programming",
                    },
                ]
            }
        }

        results = services._parse_brave_results(data)

        assert len(results) == 2
        assert results[0]["title"] == "Python Documentation"
        assert results[0]["url"] == "https://python.org/docs"
        assert results[0]["description"] == "Official Python documentation"

    def test_parse_brave_results_empty_response(self):
        """Test parsing empty Brave API response."""
        data = {"web": {"results": []}}

        results = services._parse_brave_results(data)

        assert len(results) == 0

    def test_parse_brave_results_missing_fields(self):
        """Test parsing Brave results with missing fields."""
        data = {
            "web": {
                "results": [
                    {"title": "Only Title"},
                    {"url": "https://example.com"},
                    {"description": "Only Description"},
                ]
            }
        }

        results = services._parse_brave_results(data)

        assert len(results) == 3
        assert results[0]["title"] == "Only Title"
        assert results[0]["url"] == ""
        assert results[0]["description"] == ""
        assert results[1]["title"] == ""
        assert results[1]["url"] == "https://example.com"

    def test_parse_brave_results_no_web_key(self):
        """Test parsing when 'web' key is missing."""
        data = {}

        results = services._parse_brave_results(data)

        assert len(results) == 0


class TestBraveSearchMockResults:
    """Test mock search results fallback."""

    def test_get_mock_search_results_standard(self, app_context):
        """Test generating standard mock results."""
        result = services._get_mock_search_results("artificial intelligence", 3)

        assert result["success"] is True
        assert result["source"] == "mock"
        assert result["query"] == "artificial intelligence"
        assert len(result["results"]) == 3
        assert result["total_results"] == 3
        assert "artificial intelligence" in result["results"][0]["title"]
        assert "example.com" in result["results"][0]["url"]

    def test_get_mock_search_results_max_limit(self, app_context):
        """Test mock results are limited to 5."""
        result = services._get_mock_search_results("test", 100)

        assert len(result["results"]) == 5
        assert result["total_results"] == 5

    def test_get_mock_search_results_single(self, app_context):
        """Test generating single mock result."""
        result = services._get_mock_search_results("test query", 1)

        assert len(result["results"]) == 1
        assert "Mock Result 1" in result["results"][0]["title"]


class TestBraveSearchLogging:
    """Test logging functionality for quota monitoring."""

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_search_brave_logs_request(self, mock_get, app_context, caplog):
        """Test that search requests are logged."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"web": {"results": []}}
        mock_get.return_value = mock_response

        import logging

        with caplog.at_level(logging.INFO):
            services.search_brave("test query", count=5)

        # Check that request was logged
        assert any(
            "Brave Search Request" in record.message for record in caplog.records
        )
        assert any("test query" in record.message for record in caplog.records)

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_search_brave_logs_response(self, mock_get, app_context, caplog):
        """Test that search responses are logged."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"web": {"results": []}}
        mock_get.return_value = mock_response

        import logging

        with caplog.at_level(logging.INFO):
            services.search_brave("test query")

        # Check that response was logged
        assert any(
            "Brave Search Response" in record.message for record in caplog.records
        )
        assert any("status_code" in record.message for record in caplog.records)

    @patch.dict(os.environ, {}, clear=True)
    def test_search_brave_logs_missing_api_key(self, app_context, caplog):
        """Test that missing API key is logged."""
        import logging

        with caplog.at_level(logging.WARNING):
            services.search_brave("test", fallback_to_mock=False)

        assert any(
            "Brave Search API key not configured" in record.message
            for record in caplog.records
        )

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_search_brave_logs_api_errors(self, mock_get, app_context, caplog):
        """Test that API errors are logged."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        import logging

        with caplog.at_level(logging.ERROR):
            services.search_brave("test", fallback_to_mock=False)

        assert any(
            "Brave API returned status code 500" in record.message
            for record in caplog.records
        )

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_search_brave_logs_fallback(self, mock_get, app_context, caplog):
        """Test that fallback to mock is logged."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        import logging

        with caplog.at_level(logging.INFO):
            services.search_brave("test", fallback_to_mock=True)

        assert any(
            "Falling back to mock" in record.message for record in caplog.records
        )
