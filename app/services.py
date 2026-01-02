import os
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from flask import current_app
import sendgrid
from sendgrid.helpers.mail import Mail, From, To, Content
import requests
from datetime import datetime, timezone

from .constants import (
    DEFAULT_OPENAI_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_SEARCH_COUNT,
    MAX_MOCK_RESULTS,
    DEFAULT_FROM_EMAIL,
    SEARCH_TIMEOUT,
)


# Configure OpenAI client (lazy initialization to avoid errors during testing)
def get_openai_client():
    """Get or create OpenAI client instance."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return OpenAI(api_key=api_key)
    return None


def generate_newsletter_content(topic, style="concise"):
    """
    Generate newsletter content using OpenAI.

    Args:
        topic (str): The subject of the newsletter
        style (str): Style descriptor for the content

    Returns:
        dict: Generated content with subject and body
    """
    prompt = f"""
    Create a newsletter about {topic}.
    Style: {style}
    Include:
    - An engaging subject line
    - 3-5 interesting segments with links and takeaways
    - A brief conclusion
    """

    try:
        # Get OpenAI client
        client = get_openai_client()
        if not client:
            current_app.logger.error("OpenAI API key not configured")
            return None

        # Using OpenAI v1.0+ API
        response = client.chat.completions.create(
            model=DEFAULT_OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a newsletter writer."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=DEFAULT_MAX_TOKENS,
            temperature=DEFAULT_TEMPERATURE,
        )

        # Process response to extract subject and content
        content = response.choices[0].message.content.strip()

        # Simple extraction of subject line (first line)
        lines = content.split("\n")
        subject = lines[0]
        body = "\n".join(lines[1:])

        return {"subject": subject, "content": body}
    except (APIError, APIConnectionError, RateLimitError) as e:
        current_app.logger.error(f"OpenAI API error: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"Unexpected OpenAI generation error: {str(e)}")
        return None


def send_email(to_email, subject, content):
    """
    Send email using SendGrid

    Args:
        to_email (str): Recipient email
        subject (str): Email subject line
        content (str): HTML content of the email

    Returns:
        bool: Success status
    """
    sg_api_key = os.environ.get("SENDGRID_API_KEY")
    if not sg_api_key:
        current_app.logger.error("SendGrid API key not configured")
        return False

    try:
        sg = sendgrid.SendGridAPIClient(api_key=sg_api_key)
        from_email_obj = From(DEFAULT_FROM_EMAIL)
        to_email_obj = To(to_email)
        content_obj = Content("text/html", content)

        # Use keyword arguments for clarity and correctness
        mail = Mail(
            from_email=from_email_obj,
            to_emails=to_email_obj,
            subject=subject,
            html_content=content_obj,
        )

        response = sg.client.mail.send.post(request_body=mail.get())
        return response.status_code in [200, 202]
    except Exception as e:
        current_app.logger.error(f"Email sending error: {str(e)}")
        return False


def verify_paddle_webhook(data, signature):
    """
    Verify Paddle webhook signature

    Args:
        data (dict): The webhook data
        signature (str): The webhook signature

    Returns:
        bool: Whether the signature is valid
    """
    # This is a placeholder for actual Paddle signature verification
    # In production, implement proper signature verification
    # following Paddle documentation
    return True


def search_brave(query, count=DEFAULT_SEARCH_COUNT, fallback_to_mock=True):
    """
    Search using Brave Search API with fallback mechanism.

    Args:
        query (str): The search query string
        count (int): Number of results to return (default: 10)
        fallback_to_mock (bool): Whether to use mock data if API fails

    Returns:
        dict: Search results with the following structure:
            {
                'success': bool,
                'source': str ('brave' or 'mock'),
                'query': str,
                'results': list of dicts with 'title', 'url', 'description',
                'total_results': int,
                'error': str (optional, only if success=False)
            }
    """
    brave_api_key = os.environ.get("BRAVE_SEARCH_API_KEY")

    # Log the search request
    _log_brave_search_request(query, count)

    if not brave_api_key:
        error_msg = "Brave Search API key not configured"
        current_app.logger.warning(error_msg)

        if fallback_to_mock:
            current_app.logger.info("Falling back to mock search results")
            return _get_mock_search_results(query, count)

        return {
            "success": False,
            "source": "brave",
            "query": query,
            "results": [],
            "total_results": 0,
            "error": error_msg,
        }

    try:
        # Brave Search API endpoint
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": brave_api_key,
        }
        params = {"q": query, "count": count}

        response = requests.get(url, headers=headers, params=params, timeout=SEARCH_TIMEOUT)

        # Log the API response
        _log_brave_search_response(response.status_code, query)

        if response.status_code == 200:
            data = response.json()
            parsed_results = _parse_brave_results(data)

            return {
                "success": True,
                "source": "brave",
                "query": query,
                "results": parsed_results,
                "total_results": len(parsed_results),
            }
        else:
            error_msg = f"Brave API returned status code {response.status_code}"
            current_app.logger.error(error_msg)

            if fallback_to_mock:
                current_app.logger.info(
                    "Falling back to mock search results due to API error"
                )
                return _get_mock_search_results(query, count)

            return {
                "success": False,
                "source": "brave",
                "query": query,
                "results": [],
                "total_results": 0,
                "error": error_msg,
            }

    except requests.exceptions.Timeout:
        error_msg = "Brave Search API request timed out"
        current_app.logger.error(error_msg)

        if fallback_to_mock:
            current_app.logger.info(
                "Falling back to mock search results due to timeout"
            )
            return _get_mock_search_results(query, count)

        return {
            "success": False,
            "source": "brave",
            "query": query,
            "results": [],
            "total_results": 0,
            "error": error_msg,
        }

    except Exception as e:
        error_msg = f"Brave Search error: {str(e)}"
        current_app.logger.error(error_msg)

        if fallback_to_mock:
            current_app.logger.info(
                "Falling back to mock search results due to exception"
            )
            return _get_mock_search_results(query, count)

        return {
            "success": False,
            "source": "brave",
            "query": query,
            "results": [],
            "total_results": 0,
            "error": error_msg,
        }


def _parse_brave_results(data):
    """
    Parse Brave Search API response into standardized format.

    Args:
        data (dict): Raw API response data

    Returns:
        list: List of parsed search results
    """
    results = []

    # Brave API returns results in 'web' -> 'results'
    web_results = data.get("web", {}).get("results", [])

    for item in web_results:
        result = {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
        }
        results.append(result)

    return results


def _get_mock_search_results(query, count):
    """
    Generate mock search results for fallback scenarios.

    Args:
        query (str): The search query
        count (int): Number of mock results to generate

    Returns:
        dict: Mock search results in standard format
    """
    mock_results = []
    actual_count = min(count, MAX_MOCK_RESULTS)  # Limit mock results

    for i in range(actual_count):
        mock_results.append(
            {
                "title": f'Mock Result {i+1} for "{query}"',
                "url": f"https://example.com/result/{i+1}",
                "description": f'This is a mock search result for the query "{query}". '
                f"In production, this would be replaced with real results from Brave Search API.",
            }
        )

    return {
        "success": True,
        "source": "mock",
        "query": query,
        "results": mock_results,
        "total_results": actual_count,
    }


def _log_brave_search_request(query, count):
    """
    Log Brave Search API request for quota monitoring.

    Args:
        query (str): The search query
        count (int): Number of results requested
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "brave_search",
        "action": "request",
        "query": query,
        "count": count,
    }
    current_app.logger.info(f"Brave Search Request: {log_entry}")


def _log_brave_search_response(status_code, query):
    """
    Log Brave Search API response for quota monitoring.

    Args:
        status_code (int): HTTP status code from API
        query (str): The search query
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "brave_search",
        "action": "response",
        "status_code": status_code,
        "query": query,
    }
    current_app.logger.info(f"Brave Search Response: {log_entry}")
