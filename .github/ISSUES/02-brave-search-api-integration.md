# Implement Brave Search API Integration

**Labels**: `feature`, `api-integration`, `search`, `high-priority`

## Overview
Integrate Brave Search API to gather real-time web research for newsletter topics.

## Objectives
- Implement `search_brave()` function in `app/services.py`
- Fetch relevant search results for newsletter topics
- Parse and structure search results for synthesis
- Handle API errors and rate limiting
- Cache search results when appropriate

## Technical Requirements

### API Integration
- [ ] Add `BRAVE_SEARCH_API_KEY` to configuration (already in config.py)
- [ ] Install requests library (already in requirements.txt)
- [ ] Implement Brave Search API client
- [ ] Configure search parameters (results count, freshness, safe search)
- [ ] Handle pagination if needed

### Implementation Details
- [ ] Update `search_brave(query, num_results=10)` in `app/services.py`
- [ ] Return structured results with:
  - Title
  - URL
  - Description/snippet
  - Published date (if available)
  - Relevance score
- [ ] Filter out low-quality or irrelevant results
- [ ] Handle different content types (news, articles, forums)

### Error Handling
- [ ] API key validation
- [ ] Rate limit handling with retry logic
- [ ] Network error handling
- [ ] Empty/no results scenarios
- [ ] Malformed response handling

### Caching (Optional)
- [ ] Implement Redis caching for search results
- [ ] Set appropriate cache TTL (e.g., 1 hour for news, 1 day for general)
- [ ] Cache invalidation strategy

### Testing
- [ ] Unit tests for search function
- [ ] Mock Brave API responses
- [ ] Test various query types
- [ ] Test error scenarios
- [ ] Integration test with real API (optional)

### Documentation
- [ ] Document Brave Search API usage
- [ ] Add example search responses
- [ ] Document rate limits and quotas
- [ ] Best practices for query formation

## Example Implementation

```python
import requests
from typing import List, Dict

def search_brave(query: str, num_results: int = 10) -> List[Dict]:
    """Search using Brave Search API.

    Args:
        query: Search query
        num_results: Number of results to return (max 20)

    Returns:
        List of search results with title, url, description
    """
    api_key = current_app.config.get('BRAVE_SEARCH_API_KEY')
    if not api_key:
        logger.error("Brave Search API key not configured")
        return []

    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key
    }
    params = {
        "q": query,
        "count": min(num_results, 20),
        "freshness": "pw"  # Past week for recent content
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Parse web results
        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "description": item.get("description"),
                "published": item.get("page_age"),
                "score": item.get("score", 0)
            })

        return results

    except requests.exceptions.RequestException as e:
        logger.error(f"Brave Search API error: {e}")
        return []
```

## API Documentation
- Brave Search API Docs: https://brave.com/search/api/
- Free tier: 2,000 queries/month
- Rate limit: 1 query/second

## Acceptance Criteria
- [ ] Search function returns relevant results
- [ ] API errors handled gracefully
- [ ] Tests achieve >80% coverage
- [ ] Results properly formatted for synthesis
- [ ] Documentation complete
- [ ] Code formatted with Black

## Related Issues
- Depends on: None (foundation complete)
- Blocks: Newsletter Synthesis Service

## Estimated Effort
Small (1 day)
