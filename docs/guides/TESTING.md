# Testing Guide for ThinkWrapper Newsletter Generator

## Overview

This guide provides comprehensive documentation for testing the ThinkWrapper Newsletter Generator application. Our test suite ensures platform reliability and safe feature shipping through automated unit and integration tests.

## Table of Contents

- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Coverage Requirements](#coverage-requirements)
- [Troubleshooting](#troubleshooting)
- [CI/CD Integration](#cicd-integration)

## Quick Start

### Prerequisites

- Python 3.12+
- Virtual environment activated
- Dependencies installed from `requirements.txt`

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run all tests without coverage
pytest --no-cov

# Run specific test file
pytest tests/test_routes.py

# Run specific test class
pytest tests/test_services.py::TestEmailService

# Run specific test method
pytest tests/test_services.py::TestEmailService::test_send_email_success
```

### View Coverage Report

```bash
# Terminal output
pytest

# Generate HTML report
pytest --cov-report=html
open htmlcov/index.html  # On Mac/Linux
# OR
start htmlcov/index.html  # On Windows
```

## Test Structure

Our test suite is organized into three main files:

```
tests/
├── conftest.py                     # Shared fixtures and configuration
├── test_routes.py                  # Basic route tests (3 tests)
├── test_routes_comprehensive.py   # Comprehensive route tests (17 tests)
└── test_services.py               # Service layer tests (16 tests)
```

### Test Coverage

| Module | Coverage | Tests | Status |
|--------|----------|-------|--------|
| **routes.py** | 100% | 20 tests | ✅ All passing |
| **services.py** | 95% | 16 tests | ✅ All passing |
| **Overall** | 66% | 36 tests | ✅ All passing |

## Running Tests

### Basic Commands

```bash
# Run all tests with verbose output
pytest -v

# Run tests in a specific file
pytest tests/test_services.py -v

# Run tests matching a pattern
pytest -k "email" -v

# Run tests with detailed failure information
pytest -vv --tb=long

# Run tests with less verbose output
pytest -q
```

### With Coverage

```bash
# Run with coverage (default configuration)
pytest

# Run with coverage and HTML report
pytest --cov-report=html --cov-report=term

# Run with specific coverage threshold
pytest --cov-fail-under=70

# Exclude coverage from output
pytest --no-cov
```

### Parallel Execution (Optional)

For faster test execution on multi-core systems:

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

## Writing Tests

### Test Structure Guidelines

1. **Use descriptive test names**: `test_<function>_<scenario>_<expected_result>`
2. **Organize into test classes**: Group related tests together
3. **Use fixtures**: Leverage conftest.py fixtures for setup/teardown
4. **Mock external dependencies**: Never make real API calls in tests

### Example: Writing a Route Test

```python
def test_new_endpoint_success(client):
    """Test successful response from new endpoint."""
    response = client.get('/api/new-endpoint')
    
    assert response.status_code == 200
    assert response.json['status'] == 'ok'
    assert 'data' in response.json
```

### Example: Writing a Service Test

```python
from unittest.mock import patch, Mock

class TestNewService:
    """Tests for new service functionality."""
    
    @patch('app.services.external_api')
    def test_new_service_success(self, mock_api, app_context):
        """Test successful service call."""
        # Setup mock
        mock_api.return_value = {'result': 'success'}
        
        # Call service
        result = services.new_service_function('test_input')
        
        # Assertions
        assert result is not None
        assert result['result'] == 'success'
        mock_api.assert_called_once_with('test_input')
```

### Available Fixtures

From `tests/conftest.py`:

- **`app`**: Flask application instance with TESTING=True
- **`client`**: Flask test client for making HTTP requests
- **`app_context`**: Flask application context for services that use `current_app`
- **`runner`**: Flask CLI runner for testing command-line interfaces

### Using Fixtures

```python
def test_with_app_context(app_context):
    """Test that requires Flask application context."""
    from flask import current_app
    # Now you can use current_app.logger, etc.
    assert current_app.config['TESTING'] is True

def test_with_client(client):
    """Test that makes HTTP requests."""
    response = client.get('/health')
    assert response.status_code == 200
```

### Mocking External APIs

#### OpenAI API

```python
@patch('app.services.get_openai_client')
def test_newsletter_generation(mock_get_client, app_context):
    """Test newsletter content generation."""
    # Setup mock
    mock_client = Mock()
    mock_response = Mock()
    mock_choice = Mock()
    mock_message = Mock()
    mock_message.content = "Subject: Test\n\nContent here"
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    mock_get_client.return_value = mock_client
    
    # Test
    result = services.generate_newsletter_content("AI")
    assert result is not None
```

#### SendGrid API

```python
@patch('app.services.sendgrid.SendGridAPIClient')
@patch.dict(os.environ, {'SENDGRID_API_KEY': 'test-key'})
def test_email_sending(mock_sendgrid, app_context):
    """Test email sending functionality."""
    # Setup mock
    mock_client = Mock()
    mock_response = Mock()
    mock_response.status_code = 202
    mock_client.client.mail.send.post.return_value = mock_response
    mock_sendgrid.return_value = mock_client
    
    # Test
    result = services.send_email("test@example.com", "Subject", "Content")
    assert result is True
```

## Coverage Requirements

### Current Thresholds

- **Minimum coverage**: 65%
- **Target coverage**: 80%+
- **Critical modules**: 90%+ (routes.py, services.py)

### Checking Coverage

```bash
# Check current coverage
pytest

# View coverage in browser
pytest --cov-report=html
open htmlcov/index.html
```

### Coverage Configuration

Coverage settings are in `pytest.ini`:

```ini
[coverage:run]
source = app
omit =
    */tests/*
    */venv/*
    */.venv/*
    */migrations/*
    app/models.py  # Excluded - declarative models don't need testing
```

### Improving Coverage

1. **Identify uncovered lines**: `pytest --cov-report=term-missing`
2. **Add tests for critical paths**: Focus on business logic
3. **Don't test for 100%**: Some code (like models) doesn't need tests
4. **Test edge cases**: Error handling, validation, boundary conditions

## Troubleshooting

### Common Issues

#### Issue: ImportError - No module named 'pytest'

**Solution**:
```bash
pip install -r requirements.txt
```

#### Issue: RuntimeError - Working outside of application context

**Solution**: Add `app_context` fixture to your test:
```python
def test_my_function(app_context):
    # Now current_app is available
    result = services.my_function()
```

#### Issue: Tests fail with "OpenAI API key not configured"

**Solution**: The tests use mocks, so no real API key is needed. Make sure you're using the correct mock:
```python
@patch('app.services.get_openai_client')
def test_my_function(mock_get_client, app_context):
    mock_client = Mock()
    # Setup your mock...
    mock_get_client.return_value = mock_client
```

#### Issue: Coverage too low

**Solution**:
1. Check which files are uncovered: `pytest --cov-report=term-missing`
2. Add tests for critical paths
3. Exclude non-testable code in `pytest.ini`

#### Issue: Tests are slow

**Solution**:
```bash
# Run in parallel
pip install pytest-xdist
pytest -n auto

# Run only failed tests
pytest --lf

# Run modified tests first
pytest --ff
```

### Debug Mode

```bash
# Enter debugger on failure
pytest --pdb

# Show print statements
pytest -s

# More verbose output
pytest -vv
```

## CI/CD Integration

### GitHub Actions

Our CI pipeline runs tests automatically on:
- Every push to `main`
- Every pull request
- Manual workflow dispatch

### Test Workflow

The workflow (`.github/workflows/heroku.yml`) includes:

1. **Setup**: Install Python and dependencies
2. **Test**: Run comprehensive test suite
3. **Core Tests**: Run critical route tests (always required)
4. **Code Quality**: Check formatting and linting
5. **Deploy**: Deploy to Heroku (on main branch)

### Local CI Simulation

```bash
# Run what CI runs
python scripts/run_tests.py full

# Run only core tests
python scripts/run_tests.py routes

# Run with code quality checks
pytest && black --check . && ruff check .
```

### Monitoring Test Health

- **All tests must pass** before merging to main
- **Coverage must meet minimum** threshold (65%)
- **No linting errors** allowed in new code
- **Code formatting** must follow Black standards

## Best Practices

### DO:
- ✅ Write tests for all new features
- ✅ Mock external API calls
- ✅ Use descriptive test names
- ✅ Test both success and failure cases
- ✅ Keep tests independent and isolated
- ✅ Use fixtures for common setup
- ✅ Run tests before committing

### DON'T:
- ❌ Make real API calls in tests
- ❌ Depend on external services
- ❌ Share state between tests
- ❌ Test implementation details
- ❌ Ignore failing tests
- ❌ Skip coverage checks
- ❌ Commit commented-out tests

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/3.0.x/testing/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)

## Getting Help

If you encounter issues not covered in this guide:

1. Check existing test files for examples
2. Review the conftest.py fixtures
3. Consult the pytest documentation
4. Ask in team chat or create an issue

---

**Last Updated**: 2026-01-01
**Test Coverage**: 66% (36/36 tests passing)
**Status**: ✅ All systems operational
