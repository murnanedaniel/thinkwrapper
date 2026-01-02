"""
End-to-end test for Brave Search API integration.

This test demonstrates a real-world usage scenario of the Brave Search API
integration, including successful searches and fallback handling.
"""

import pytest
import os
from unittest.mock import patch, Mock
from app import create_app, services


class TestBraveSearchEndToEnd:
    """End-to-end tests for Brave Search integration."""

    @pytest.fixture
    def app(self):
        """Create a test Flask application."""
        app = create_app({"TESTING": True})
        return app

    @pytest.fixture
    def app_context(self, app):
        """Create an application context for tests."""
        with app.app_context():
            yield app

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_end_to_end_successful_search(self, mock_get, app_context):
        """
        End-to-end test: Successful Brave Search query returns parsed results.

        This simulates a real user scenario where:
        1. User queries for "Python programming tutorials"
        2. Brave API returns relevant search results
        3. Results are parsed and returned in standardized format
        4. All requests/responses are logged for monitoring
        """
        # Mock a realistic Brave API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "Python.org Official Tutorial",
                        "url": "https://docs.python.org/3/tutorial/",
                        "description": "The official Python tutorial covers basic concepts and features of the Python language and system.",
                    },
                    {
                        "title": "Real Python - Python Tutorials",
                        "url": "https://realpython.com/",
                        "description": "Real Python provides high-quality Python tutorials and resources for developers of all skill levels.",
                    },
                    {
                        "title": "Learn Python - Free Interactive Python Tutorial",
                        "url": "https://www.learnpython.org/",
                        "description": "Learn Python with interactive tutorials and examples. Perfect for beginners.",
                    },
                ]
            }
        }
        mock_get.return_value = mock_response

        # Execute the search
        results = services.search_brave("Python programming tutorials", count=10)

        # Verify the results
        assert results is not None, "Results should not be None"
        assert results["success"] is True, "Search should be successful"
        assert results["source"] == "brave", "Source should be Brave API"
        assert results["query"] == "Python programming tutorials", "Query should match"
        assert results["total_results"] == 3, "Should return 3 results"

        # Verify individual result structure
        first_result = results["results"][0]
        assert "title" in first_result, "Result should have title"
        assert "url" in first_result, "Result should have URL"
        assert "description" in first_result, "Result should have description"
        assert first_result["title"] == "Python.org Official Tutorial"
        assert "python.org" in first_result["url"]

        # Verify API was called correctly
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["params"]["q"] == "Python programming tutorials"
        assert call_kwargs["params"]["count"] == 10
        assert call_kwargs["headers"]["X-Subscription-Token"] == "test-api-key"
        assert call_kwargs["timeout"] == 10

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_end_to_end_api_failure_with_fallback(self, mock_get, app_context, caplog):
        """
        End-to-end test: API failure triggers fallback to mock results.

        This simulates a real-world failure scenario where:
        1. User queries for "machine learning"
        2. Brave API returns an error (e.g., rate limit exceeded)
        3. System automatically falls back to mock results
        4. User still receives results (though mock) and operation doesn't fail
        5. All events are logged for monitoring
        """
        # Mock an API error response
        mock_response = Mock()
        mock_response.status_code = 429  # Too Many Requests
        mock_get.return_value = mock_response

        import logging

        with caplog.at_level(logging.INFO):
            # Execute the search with fallback enabled (default)
            results = services.search_brave("machine learning", count=5)

        # Verify fallback was triggered
        assert results is not None, "Results should not be None"
        assert results["success"] is True, "Search should still succeed via fallback"
        assert results["source"] == "mock", "Source should be mock (fallback)"
        assert results["query"] == "machine learning", "Query should match"
        assert len(results["results"]) > 0, "Should have mock results"

        # Verify logging captured the fallback
        assert any(
            "Brave API returned status code 429" in record.message
            for record in caplog.records
        )
        assert any(
            "Falling back to mock" in record.message for record in caplog.records
        )

        # Verify mock results have correct structure
        for result in results["results"]:
            assert "title" in result
            assert "url" in result
            assert "description" in result
            assert "machine learning" in result["title"]

    @patch.dict(os.environ, {}, clear=True)
    def test_end_to_end_no_api_key_with_fallback(self, app_context, caplog):
        """
        End-to-end test: Missing API key triggers fallback to mock results.

        This simulates a real scenario where:
        1. Developer hasn't configured Brave API key yet
        2. Application still works using mock results
        3. Warning is logged about missing API key
        4. User can continue development/testing without API key
        """
        import logging

        with caplog.at_level(logging.INFO):
            # Execute search without API key
            results = services.search_brave("test query", count=3)

        # Verify fallback was triggered
        assert results is not None
        assert results["success"] is True
        assert results["source"] == "mock"
        assert len(results["results"]) == 3

        # Verify warning was logged
        assert any(
            "Brave Search API key not configured" in record.message
            for record in caplog.records
        )
        assert any(
            "Falling back to mock" in record.message for record in caplog.records
        )

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_end_to_end_timeout_with_fallback(self, mock_get, app_context, caplog):
        """
        End-to-end test: Network timeout triggers fallback to mock results.

        This simulates a real scenario where:
        1. User makes a search query
        2. Brave API request times out (slow network, API issues)
        3. System automatically falls back to mock results
        4. User experience is not interrupted
        """
        import requests

        mock_get.side_effect = requests.exceptions.Timeout(
            "Request timed out after 10 seconds"
        )

        import logging

        with caplog.at_level(logging.ERROR):
            results = services.search_brave("neural networks")

        # Verify fallback worked
        assert results["success"] is True
        assert results["source"] == "mock"
        assert "neural networks" in results["results"][0]["title"]

        # Verify timeout was logged
        assert any("timed out" in record.message for record in caplog.records)

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_end_to_end_no_fallback_scenario(self, mock_get, app_context):
        """
        End-to-end test: Search without fallback returns error on API failure.

        This simulates a scenario where:
        1. Application explicitly wants to know if Brave API fails
        2. No fallback is desired (fallback_to_mock=False)
        3. API error returns proper error structure
        4. Application can handle the error appropriately
        """
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        # Execute search with fallback disabled
        results = services.search_brave("test", fallback_to_mock=False)

        # Verify error is returned properly
        assert results["success"] is False
        assert results["source"] == "brave"
        assert "error" in results
        assert "status code 500" in results["error"]
        assert len(results["results"]) == 0

    @patch("app.services.requests.get")
    @patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test-api-key"})
    def test_end_to_end_integration_with_newsletter_workflow(
        self, mock_get, app_context
    ):
        """
        End-to-end test: Integration with newsletter generation workflow.

        This demonstrates how Brave Search would be used in a real newsletter
        generation workflow:
        1. User wants to create a newsletter about "AI trends"
        2. System uses Brave Search to find relevant articles
        3. Search results provide URLs and descriptions
        4. Newsletter generator can use these to create content with references
        """
        # Mock realistic search results for a newsletter topic
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "Top AI Trends in 2024",
                        "url": "https://example.com/ai-trends-2024",
                        "description": "Explore the latest trends in artificial intelligence including LLMs, computer vision, and ethical AI.",
                    },
                    {
                        "title": "Generative AI Revolution",
                        "url": "https://example.com/gen-ai-revolution",
                        "description": "How generative AI is transforming industries from healthcare to entertainment.",
                    },
                    {
                        "title": "AI Ethics and Regulation",
                        "url": "https://example.com/ai-ethics",
                        "description": "Understanding the ethical considerations and regulatory landscape for AI technologies.",
                    },
                ]
            }
        }
        mock_get.return_value = mock_response

        # Simulate newsletter workflow
        newsletter_topic = "AI trends"

        # Step 1: Search for relevant articles
        search_results = services.search_brave(newsletter_topic, count=5)

        # Step 2: Verify search was successful
        assert search_results["success"] is True
        assert len(search_results["results"]) > 0

        # Step 3: Extract article information for newsletter
        articles_for_newsletter = []
        for result in search_results["results"]:
            article = {
                "title": result["title"],
                "url": result["url"],
                "summary": result["description"],
            }
            articles_for_newsletter.append(article)

        # Step 4: Verify we have articles ready for newsletter generation
        assert len(articles_for_newsletter) == 3
        assert all("title" in article for article in articles_for_newsletter)
        assert all("url" in article for article in articles_for_newsletter)
        assert all("summary" in article for article in articles_for_newsletter)

        # This demonstrates how the search results can be integrated
        # into a newsletter template or passed to an AI to generate content
        first_article = articles_for_newsletter[0]
        assert "AI Trends" in first_article["title"]
        assert first_article["url"].startswith("https://")
        assert len(first_article["summary"]) > 20  # Has meaningful description
