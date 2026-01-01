"""
Pytest configuration and fixtures for ThinkWrapper tests.

This module provides shared fixtures and test configuration
to ensure proper test isolation and Flask application context.
"""

import pytest
from app import create_app


@pytest.fixture(scope="function")
def app():
    """
    Create and configure a Flask application instance for testing.

    Returns:
        Flask: Configured Flask application with TESTING=True
    """
    app = create_app({"TESTING": True})
    return app


@pytest.fixture(scope="function")
def client(app):
    """
    Create a test client for the Flask application.

    Args:
        app: Flask application fixture

    Returns:
        FlaskClient: Test client for making HTTP requests
    """
    return app.test_client()


@pytest.fixture(scope="function")
def app_context(app):
    """
    Create a Flask application context for tests that need it.

    This fixture is useful for service tests that need access to
    current_app, logger, etc. outside of a request context.

    Args:
        app: Flask application fixture

    Yields:
        Flask application context
    """
    with app.app_context():
        yield app


@pytest.fixture(scope="function")
def runner(app):
    """
    Create a test CLI runner for the Flask application.

    Args:
        app: Flask application fixture

    Returns:
        FlaskCliRunner: CLI test runner
    """
    return app.test_cli_runner()
