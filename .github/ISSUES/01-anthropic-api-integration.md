# Implement Anthropic Claude API Integration

**Labels**: `feature`, `api-integration`, `ai`, `high-priority`

## Overview
Integrate Anthropic Claude API for AI-powered newsletter generation using the Deep Research capability.

## Objectives
- Replace stubbed `generate_newsletter_content()` function in `app/services.py`
- Implement Anthropic Claude API client
- Use Claude's deep research capabilities for comprehensive topic analysis
- Handle API errors and rate limiting gracefully
- Add retry logic with exponential backoff

## Technical Requirements

### API Integration
- [ ] Install and configure `anthropic` Python package (already in requirements.txt)
- [ ] Create Anthropic client with proper API key management from config
- [ ] Implement newsletter generation using Claude 3.5 Sonnet or Opus
- [ ] Use extended thinking/research mode for comprehensive analysis
- [ ] Configure appropriate temperature and token limits

### Implementation Details
- [ ] Update `generate_newsletter_content(topic, style="concise")` in `app/services.py`
- [ ] Return structured response with:
  - Newsletter subject line
  - Main content sections
  - Key takeaways
  - Suggested links/resources
- [ ] Add proper error handling for:
  - API key missing/invalid
  - Rate limiting
  - Network errors
  - Invalid responses

### Testing
- [ ] Write unit tests for newsletter generation
- [ ] Mock Anthropic API for testing
- [ ] Test error scenarios (rate limits, network failures)
- [ ] Integration test with real API (optional, requires API key)
- [ ] Test different topics and styles

### Documentation
- [ ] Document API usage in code comments
- [ ] Add example API responses
- [ ] Update README with Anthropic API key instructions
- [ ] Document rate limits and best practices

## Example Implementation

```python
from anthropic import Anthropic

def generate_newsletter_content(topic, style="concise"):
    """Generate newsletter using Anthropic Claude."""
    client = Anthropic(api_key=current_app.config['ANTHROPIC_API_KEY'])

    prompt = f"""Please create a comprehensive newsletter about {topic}.

Style: {style}

Include:
- An engaging subject line
- 3-5 well-researched sections with key insights
- Relevant statistics or data points
- Actionable takeaways
- Suggested resources for further reading

Format the response as JSON with fields: subject, sections[], takeaways[], resources[]
"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse and return structured response
    return parse_newsletter_response(response.content)
```

## Acceptance Criteria
- [ ] Newsletter generation works end-to-end
- [ ] API errors are handled gracefully
- [ ] Tests achieve >80% coverage
- [ ] Documentation is complete
- [ ] Code follows project style (Black formatted)

## Related Issues
- Depends on: None (foundation complete)
- Blocks: Newsletter Synthesis Service

## Estimated Effort
Medium (1-2 days)
