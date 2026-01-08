import os
import logging
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from mailjet_rest import Client
import requests
from datetime import datetime, timezone, timedelta

from .constants import (
    DEFAULT_OPENAI_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_SEARCH_COUNT,
    MAX_MOCK_RESULTS,
    DEFAULT_FROM_EMAIL,
    SEARCH_TIMEOUT,
)

# Module-level logger that works outside Flask context
logger = logging.getLogger(__name__)


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
            logger.error("OpenAI API key not configured")
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
        logger.error(f"OpenAI API error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected OpenAI generation error: {str(e)}")
        return None


def send_email(to_email, subject, content):
    """
    Send email using Mailjet

    Args:
        to_email (str): Recipient email
        subject (str): Email subject line
        content (str): HTML content of the email

    Returns:
        bool: Success status
    """
    mailjet_api_key = os.environ.get("MAILJET_API_KEY")
    mailjet_api_secret = os.environ.get("MAILJET_API_SECRET")
    
    if not mailjet_api_key:
        logger.error("Mailjet API key not configured")
        return False
    
    if not mailjet_api_secret:
        logger.error("Mailjet API secret not configured")
        return False

    try:
        mailjet = Client(auth=(mailjet_api_key, mailjet_api_secret), version='v3.1')
        
        data = {
            'Messages': [
                {
                    "From": {
                        "Email": DEFAULT_FROM_EMAIL,
                        "Name": "ThinkWrapper"
                    },
                    "To": [
                        {
                            "Email": to_email
                        }
                    ],
                    "Subject": subject,
                    "HTMLPart": content
                }
            ]
        }
        
        result = mailjet.send.create(data=data)
        logger.info(f"Mailjet API response: status={result.status_code}, body={result.json()}")
        
        if result.status_code not in [200, 201]:
            logger.error(f"Mailjet API error: {result.status_code} - {result.json()}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Email sending error: {str(e)}", exc_info=True)
        return False


def get_freshness_from_schedule(schedule):
    """
    Convert newsletter schedule to Brave Search freshness parameter.
    
    Args:
        schedule (str): Newsletter schedule ('daily', 'weekly', 'biweekly', 'monthly')
    
    Returns:
        str: Brave Search freshness parameter ('pd', 'pw', 'pm') or None
    """
    schedule_to_freshness = {
        'daily': 'pd',      # past day
        'weekly': 'pw',     # past week
        'biweekly': 'pw',   # past week (closest match)
        'monthly': 'pm',    # past month
    }
    return schedule_to_freshness.get(schedule.lower())


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


def search_brave(query, count=DEFAULT_SEARCH_COUNT, fallback_to_mock=True, freshness=None, search_type='web'):
    """
    Search using Brave Search API (Web or News) with fallback mechanism.

    Args:
        query (str): The search query string
        count (int): Number of results to return (default: 10)
        fallback_to_mock (bool): Whether to use mock data if API fails
        freshness (str): Time filter - 'pd' (past day), 'pw' (past week), 
                        'pm' (past month), 'py' (past year), or None for any time
        search_type (str): Type of search - 'web' or 'news' (default: 'web')

    Returns:
        dict: Search results with the following structure:
            {
                'success': bool,
                'source': str ('brave_web', 'brave_news', or 'mock'),
                'query': str,
                'results': list of dicts with 'title', 'url', 'description',
                'total_results': int,
                'error': str (optional, only if success=False)
            }
    """
    brave_api_key = os.environ.get("BRAVE_SEARCH_API_KEY")

    # Log the search request
    _log_brave_search_request(query, count, search_type)

    if not brave_api_key:
        error_msg = "Brave Search API key not configured"
        logger.warning(error_msg)

        if fallback_to_mock:
            logger.info("Falling back to mock search results")
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
        # Brave Search API endpoint - web or news
        if search_type == 'news':
            url = "https://api.search.brave.com/res/v1/news/search"
            source_type = "brave_news"
        else:
            url = "https://api.search.brave.com/res/v1/web/search"
            source_type = "brave_web"
            
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": brave_api_key,
        }
        params = {"q": query, "count": count}
        
        # Add freshness filter if specified
        if freshness:
            params["freshness"] = freshness

        response = requests.get(url, headers=headers, params=params, timeout=SEARCH_TIMEOUT)

        # Log the API response
        _log_brave_search_response(response.status_code, query, search_type)

        if response.status_code == 200:
            data = response.json()
            parsed_results = _parse_brave_results(data, search_type)

            return {
                "success": True,
                "source": source_type,
                "query": query,
                "results": parsed_results,
                "total_results": len(parsed_results),
            }
        else:
            error_msg = f"Brave {search_type.upper()} API returned status code {response.status_code}"
            logger.error(error_msg)

            if fallback_to_mock:
                logger.info(
                    "Falling back to mock search results due to API error"
                )
                return _get_mock_search_results(query, count)

            return {
                "success": False,
                "source": source_type,
                "query": query,
                "results": [],
                "total_results": 0,
                "error": error_msg,
            }

    except requests.exceptions.Timeout:
        error_msg = "Brave Search API request timed out"
        logger.error(error_msg)

        if fallback_to_mock:
            logger.info(
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
        logger.error(error_msg)

        if fallback_to_mock:
            logger.info(
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


def _parse_brave_results(data, search_type='web'):
    """
    Parse Brave Search API response into standardized format.

    Args:
        data (dict): Raw API response data
        search_type (str): Type of search - 'web' or 'news'

    Returns:
        list: List of parsed search results
    """
    results = []

    if search_type == 'news':
        # News API returns results in 'results' array
        news_results = data.get("results", [])
        for item in news_results:
            result = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
                "age": item.get("age", ""),  # News articles have age field
            }
            results.append(result)
    else:
        # Web API returns results in 'web' -> 'results'
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


def search_arxiv(query, count=DEFAULT_SEARCH_COUNT, freshness=None):
    """
    Search arXiv for academic papers using the arxiv.py library.
    
    Args:
        query (str): The search query string
        count (int): Number of results to return (default: 10)
        freshness (str): Time filter - 'pd' (past day), 'pw' (past week), 
                        'pm' (past month), 'py' (past year), or None for any time
    
    Returns:
        dict: Search results with the following structure:
            {
                'success': bool,
                'source': 'arxiv',
                'query': str,
                'results': list of dicts with 'title', 'url', 'description', 'published',
                'total_results': int,
                'error': str (optional, only if success=False)
            }
    """
    try:
        import arxiv
        
        # Log the search request
        _log_arxiv_search_request(query, count, freshness)
        
        # Calculate date threshold based on freshness
        date_threshold = None
        if freshness:
            now = datetime.now(timezone.utc)
            if freshness == 'pd':  # past day
                date_threshold = now - timedelta(days=1)
            elif freshness == 'pw':  # past week
                date_threshold = now - timedelta(days=7)
            elif freshness == 'pm':  # past month
                date_threshold = now - timedelta(days=30)
            elif freshness == 'py':  # past year
                date_threshold = now - timedelta(days=365)
        
        # Create search with most recent results first
        search = arxiv.Search(
            query=query,
            max_results=count * 3,  # Fetch more to account for date filtering
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        # Create default client
        client = arxiv.Client()
        
        # Fetch and parse results
        results = []
        for paper in client.results(search):
            # Filter by date if threshold specified
            if date_threshold and paper.published < date_threshold:
                continue
            
            result = {
                'title': paper.title,
                'url': paper.entry_id,  # Direct link to arXiv paper
                'description': paper.summary[:500],  # Truncate long abstracts
                'published': paper.published.isoformat(),
                'authors': ', '.join([author.name for author in paper.authors[:3]]),  # First 3 authors
            }
            results.append(result)
            
            # Stop once we have enough results
            if len(results) >= count:
                break
        
        _log_arxiv_search_response(len(results), query, freshness)
        
        return {
            'success': True,
            'source': 'arxiv',
            'query': query,
            'results': results,
            'total_results': len(results),
        }
        
    except ImportError:
        error_msg = "arXiv library not installed. Run: pip install arxiv"
        logger.error(error_msg)
        return {
            'success': False,
            'source': 'arxiv',
            'query': query,
            'results': [],
            'total_results': 0,
            'error': error_msg,
        }
    except Exception as e:
        error_msg = f"arXiv search error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'source': 'arxiv',
            'query': query,
            'results': [],
            'total_results': 0,
            'error': error_msg,
        }


def _log_arxiv_search_request(query, count, freshness=None):
    """
    Log arXiv search request.
    
    Args:
        query (str): The search query
        count (int): Number of results requested
        freshness (str): Time filter applied
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "arxiv",
        "action": "request",
        "query": query,
        "count": count,
        "freshness": freshness,
    }
    logger.info(f"arXiv Search Request: {log_entry}")


def _log_arxiv_search_response(result_count, query, freshness=None):
    """
    Log arXiv search response.
    
    Args:
        result_count (int): Number of results returned
        query (str): The search query
        freshness (str): Time filter applied
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "arxiv",
        "action": "response",
        "result_count": result_count,
        "query": query,
        "freshness": freshness,
    }
    logger.info(f"arXiv Search Response: {log_entry}")


def _log_brave_search_request(query, count, search_type='web'):
    """
    Log Brave Search API request for quota monitoring.

    Args:
        query (str): The search query
        count (int): Number of results requested
        search_type (str): Type of search - 'web' or 'news'
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": f"brave_{search_type}",
        "action": "request",
        "query": query,
        "count": count,
    }
    logger.info(f"Brave {search_type.upper()} Search Request: {log_entry}")


def _log_brave_search_response(status_code, query, search_type='web'):
    """
    Log Brave Search API response for quota monitoring.

    Args:
        status_code (int): HTTP status code from API
        query (str): The search query
        search_type (str): Type of search - 'web' or 'news'
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": f"brave_{search_type}",
        "action": "response",
        "status_code": status_code,
        "query": query,
    }
    logger.info(f"Brave {search_type.upper()} Search Response: {log_entry}")
