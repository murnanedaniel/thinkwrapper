"""
Claude API Service Module

This module provides integration with the Anthropic Claude API for AI-driven
natural language processing capabilities. It supports both synchronous and
asynchronous requests.

Environment Variables Required:
    ANTHROPIC_API_KEY: Your Anthropic API key (can be set in .env file)
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import Message

# Module-level logger that works outside Flask context
logger = logging.getLogger(__name__)


# Initialize Claude clients
def _get_api_key() -> Optional[str]:
    """Get the Anthropic API key from environment variables."""
    return os.environ.get('ANTHROPIC_API_KEY')


def _get_client() -> Optional[Anthropic]:
    """Get a synchronous Claude client."""
    api_key = _get_api_key()
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def _get_async_client() -> Optional[AsyncAnthropic]:
    """Get an asynchronous Claude client."""
    api_key = _get_api_key()
    if not api_key:
        return None
    return AsyncAnthropic(api_key=api_key)


def format_prompt(
    topic: str,
    style: str = "professional",
    additional_context: Optional[str] = None,
    max_length: Optional[str] = None
) -> str:
    """
    Format a prompt for Claude API with consistent structure.
    
    Args:
        topic: The main topic or subject for the prompt
        style: The desired style (e.g., "professional", "casual", "technical")
        additional_context: Any additional context to include
        max_length: Desired length of the response (e.g., "brief", "detailed", "comprehensive")
        
    Returns:
        A formatted prompt string ready for Claude API
        
    Examples:
        >>> format_prompt("AI trends", style="technical", max_length="brief")
        "Write about AI trends in a technical style. Keep the response brief..."
    """
    prompt_parts = [f"Write about {topic}"]
    
    if style:
        prompt_parts.append(f"in a {style} style")
    
    if max_length:
        prompt_parts.append(f"Keep the response {max_length}")
    
    if additional_context:
        prompt_parts.append(f"Additional context: {additional_context}")
    
    return ". ".join(prompt_parts) + "."


def parse_response(message: Message) -> Dict[str, Any]:
    """
    Parse Claude API response into a standardized format.
    
    Args:
        message: The Message object from Claude API
        
    Returns:
        A dictionary with parsed response data including:
            - text: The main text content
            - model: The model used
            - usage: Token usage statistics
            - stop_reason: Why the response stopped
            
    Examples:
        >>> parsed = parse_response(claude_response)
        >>> print(parsed['text'])
    """
    # Extract text content from the response
    text_content = ""
    for content_block in message.content:
        if hasattr(content_block, 'text'):
            text_content += content_block.text
    
    return {
        'text': text_content,
        'model': message.model,
        'usage': {
            'input_tokens': message.usage.input_tokens,
            'output_tokens': message.usage.output_tokens,
        },
        'stop_reason': message.stop_reason,
        'id': message.id,
    }


def generate_text(
    prompt: str,
    model: str = "claude-haiku-4-5",
    max_tokens: int = 1024,
    temperature: float = 1.0,
    system_prompt: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Generate text using Claude API (synchronous).
    
    Args:
        prompt: The prompt to send to Claude
        model: The Claude model to use (default: claude-3-5-sonnet-20241022)
        max_tokens: Maximum tokens in the response
        temperature: Randomness in responses (0.0 to 1.0)
        system_prompt: Optional system prompt to set context
        
    Returns:
        Parsed response dictionary or None on error
        
    Examples:
        >>> result = generate_text("Explain quantum computing")
        >>> print(result['text'])
    """
    client = _get_client()
    
    if not client:
        logger.error("Anthropic API key not configured")
        return None

    try:
        # Build message parameters
        message_params = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        # Add system prompt if provided
        if system_prompt:
            message_params["system"] = system_prompt

        # Make API call
        message = client.messages.create(**message_params)

        # Parse and return response
        return parse_response(message)

    except Exception as e:
        logger.error(f"Claude API error: {str(e)}")
        return None


async def generate_text_async(
    prompt: str,
    model: str = "claude-haiku-4-5",
    max_tokens: int = 1024,
    temperature: float = 1.0,
    system_prompt: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Generate text using Claude API (asynchronous).
    
    Args:
        prompt: The prompt to send to Claude
        model: The Claude model to use (default: claude-3-5-sonnet-20241022)
        max_tokens: Maximum tokens in the response
        temperature: Randomness in responses (0.0 to 1.0)
        system_prompt: Optional system prompt to set context
        
    Returns:
        Parsed response dictionary or None on error
        
    Examples:
        >>> result = await generate_text_async("Explain quantum computing")
        >>> print(result['text'])
    """
    client = _get_async_client()

    if not client:
        logger.error("Anthropic API key not configured")
        return None

    try:
        # Build message parameters
        message_params = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        # Add system prompt if provided
        if system_prompt:
            message_params["system"] = system_prompt

        # Make async API call
        message = await client.messages.create(**message_params)

        # Parse and return response
        return parse_response(message)

    except Exception as e:
        logger.error(f"Claude API error (async): {str(e)}")
        return None


def generate_newsletter_content_claude(
    topic: str,
    style: str = "professional",
    max_tokens: int = 2000
) -> Optional[Dict[str, str]]:
    """
    Generate newsletter content using Claude API.
    
    This is a convenience function specifically for newsletter generation,
    demonstrating how to use Claude for the ThinkWrapper use case.
    
    Args:
        topic: The newsletter topic
        style: The writing style
        max_tokens: Maximum tokens for the response
        
    Returns:
        Dictionary with 'subject' and 'content' keys, or None on error
        
    Examples:
        >>> newsletter = generate_newsletter_content_claude("AI trends", "technical")
        >>> print(newsletter['subject'])
        >>> print(newsletter['content'])
    """
    # Create a specialized prompt for newsletter generation
    prompt = f"""Create a newsletter about {topic}.
    
Style: {style}

Please structure your response as follows:
1. Start with a compelling subject line on the first line (prefix with "Subject: ")
2. Follow with the newsletter body including:
   - An engaging introduction
   - 3-5 interesting segments with key insights
   - Links to relevant resources (use placeholder URLs)
   - A brief conclusion

Keep the tone {style} and make it engaging for readers."""
    
    # Use a system prompt to reinforce the newsletter format
    system_prompt = """You are an expert newsletter writer. Your newsletters are clear, 
engaging, and well-structured. Always start with a subject line prefixed with "Subject: " 
on the first line, followed by the newsletter content."""
    
    # Generate content
    result = generate_text(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.7,
        system_prompt=system_prompt
    )
    
    if not result:
        return None
    
    # Parse the response to extract subject and body
    content = result['text'].strip()
    lines = content.split('\n', 1)
    
    # Extract subject line
    subject = lines[0]
    if subject.lower().startswith('subject:'):
        subject = subject[8:].strip()
    
    # Extract body (everything after the first line)
    body = lines[1].strip() if len(lines) > 1 else ""
    
    return {
        'subject': subject,
        'content': body,
        'model': result['model'],
        'usage': result['usage']
    }


def _sanitize_text_for_prompt(text: str) -> str:
    """
    Sanitize text from external sources to prevent prompt injection.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text safe for use in prompts
    """
    if not text:
        return ""
    
    # Remove or escape potentially problematic characters/sequences
    # Replace newlines with spaces to prevent prompt structure manipulation
    sanitized = text.replace('\n', ' ').replace('\r', ' ')
    
    # Remove multiple spaces
    sanitized = ' '.join(sanitized.split())
    
    # Limit length to prevent token overflow from malicious input
    max_length = 500
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized


def generate_search_topics(
    main_topic: str,
    num_topics: int = 5
) -> Optional[List[str]]:
    """
    Generate search topic seeds using Claude Haiku for comprehensive newsletter research.
    
    Uses Haiku for fast, cost-effective topic generation before the main search.
    
    Args:
        main_topic: The main newsletter topic
        num_topics: Number of search topics to generate (default: 5)
        
    Returns:
        List of search topic strings, or None on error
        
    Examples:
        >>> topics = generate_search_topics("AI trends in healthcare")
        >>> print(topics)
        ['AI medical diagnosis breakthroughs', 'machine learning drug discovery', ...]
    """
    prompt = (
        f"I'm creating a newsletter about: {main_topic}\n\n"
        f"Please suggest {num_topics} specific, diverse search queries that would help me find "
        f"the most relevant and current information for this newsletter. "
        f"Each query should target a different aspect or angle of the topic.\n\n"
        f"Respond with ONLY the search queries, one per line, without numbering or bullets."
    )
    
    system_prompt = (
        "You are a research assistant helping to find diverse, relevant content for newsletters. "
        "Generate search queries that are specific, actionable, and likely to return high-quality results."
    )
    
    # Use Haiku for fast, cost-effective topic generation
    result = generate_text(
        prompt=prompt,
        model="claude-haiku-4-5",
        max_tokens=300,
        temperature=0.8,  # Slightly higher for creative query generation
        system_prompt=system_prompt
    )
    
    if not result:
        logger.error(f"Failed to generate search topics for: {main_topic}")
        return None
    
    # Parse the response into a list of topics
    topics_text = result['text'].strip()
    topics = [line.strip() for line in topics_text.split('\n') if line.strip()]
    
    # Remove any numbering or bullets that might have been included
    topics = [topic.lstrip('0123456789.-•* ') for topic in topics]
    
    logger.info(f"Generated {len(topics)} search topics for '{main_topic}': {topics}")
    return topics[:num_topics]  # Ensure we don't exceed the requested number


def generate_newsletter_with_search(
    topic: str,
    style: str = "professional",
    max_tokens: int = 2000,
    search_count: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Generate newsletter content using Claude API with real search results from Brave Search.
    
    This function integrates Brave Search to get current, real articles and then uses
    Claude to synthesize them into a compelling newsletter with verified links.
    
    Args:
        topic: The newsletter topic
        style: The writing style
        max_tokens: Maximum tokens for the response
        search_count: Number of search results to fetch from Brave Search
        
    Returns:
        Dictionary with 'subject', 'content', 'articles', and metadata, or None on error
        
    Examples:
        >>> newsletter = generate_newsletter_with_search("AI trends", "technical")
        >>> print(newsletter['subject'])
        >>> print(newsletter['content'])
        >>> print(newsletter['articles'])  # List of real articles used
    """
    from .services import search_brave
    
    # Get real search results from Brave Search
    logger.info(f"Searching Brave for topic: {topic}")
    search_results = search_brave(query=topic, count=search_count, fallback_to_mock=False)
    
    if not search_results.get('success') or not search_results.get('results'):
        logger.error(f"Failed to get search results for topic: {topic}")
        return None
    
    articles = search_results['results']
    logger.info(f"Retrieved {len(articles)} articles from {search_results['source']}")
    
    # Sanitize and format articles for the prompt
    articles_text = "\n\n".join([
        f"Article {i+1}:\n"
        f"Title: {_sanitize_text_for_prompt(article.get('title', ''))}\n"
        f"URL: {_sanitize_text_for_prompt(article.get('url', ''))}\n"
        f"Description: {_sanitize_text_for_prompt(article.get('description', ''))}"
        for i, article in enumerate(articles[:10])  # Limit to top 10 to avoid token overflow
    ])
    
    # Create a specialized prompt with real article data
    prompt = (
        f"Create a newsletter about {topic} using the following real articles as sources.\n\n"
        f"Style: {style}\n\n"
        f"Real Articles to Reference:\n{articles_text}\n\n"
        f"Please structure your response as follows:\n"
        f"1. Start with a compelling subject line on the first line (prefix with \"Subject: \")\n"
        f"2. Follow with the newsletter body including:\n"
        f"   - An engaging introduction\n"
        f"   - 3-5 interesting segments synthesizing insights from the articles above\n"
        f"   - Include REAL URLs from the articles provided (not placeholder URLs)\n"
        f"   - Reference specific articles by title and include their actual URLs\n"
        f"   - A brief conclusion\n\n"
        f"IMPORTANT: Use only the real URLs provided above. Do not make up or hallucinate any URLs.\n"
        f"Keep the tone {style} and make it engaging for readers."
    )
    
    # Use a system prompt to reinforce using real data
    system_prompt = (
        "You are an expert newsletter writer who synthesizes real articles into "
        "compelling newsletters. You MUST use only the real article URLs provided to you - never make up "
        "or hallucinate URLs. Always start with a subject line prefixed with \"Subject: \" on the first line, "
        "followed by the newsletter content with real, verified links from the provided articles."
    )
    
    # Generate content
    result = generate_text(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.7,
        system_prompt=system_prompt
    )
    
    if not result:
        return None
    
    # Parse the response to extract subject and body
    content = result['text'].strip()
    lines = content.split('\n', 1)
    
    # Extract subject line
    subject = lines[0]
    if subject.lower().startswith('subject:'):
        subject = subject[8:].strip()
    
    # Extract body (everything after the first line)
    body = lines[1].strip() if len(lines) > 1 else ""
    
    return {
        'subject': subject,
        'content': body,
        'articles': articles,
        'search_source': search_results['source'],
        'total_articles': len(articles),
        'model': result['model'],
        'usage': result['usage']
    }


def generate_newsletter_with_multi_search(
    topic: str,
    schedule: str = 'weekly',
    style: str = "professional",
    max_tokens: int = 2000,
    progress_callback=None
) -> Optional[Dict[str, Any]]:
    """
    Generate newsletter using Claude with multi-topic Brave Search and progress tracking.
    
    This refactored version uses modular components for better maintainability:
    - ProgressTracker: Consistent progress reporting
    - SearchOrchestrator: Multi-topic search coordination  
    - NewsletterBuilder: Content assembly and generation
    
    Args:
        topic: The main newsletter topic
        schedule: Newsletter schedule ('daily', 'weekly', 'monthly', 'biweekly')
        style: The writing style
        max_tokens: Maximum tokens for the response
        progress_callback: Optional callback function for progress updates
        
    Returns:
        Dictionary with 'subject', 'content', 'articles', 'search_topics', and metadata
        
    Examples:
        >>> newsletter = generate_newsletter_with_multi_search("AI trends", "weekly")
    """
    from .progress_tracker import ProgressTracker
    from .search_orchestrator import SearchOrchestrator
    from .newsletter_builder import NewsletterBuilder
    
    try:
        # Initialize components
        tracker = ProgressTracker(callback=progress_callback)
        orchestrator = SearchOrchestrator(progress_tracker=tracker)
        builder = NewsletterBuilder(progress_tracker=tracker)
        
        # Execute multi-topic search
        search_results = orchestrator.execute_multi_search(
            main_topic=topic,
            schedule=schedule,
            num_topics=5,
            results_per_topic=10
        )
        
        # Build newsletter from results
        newsletter = builder.build(
            topic=topic,
            articles=search_results['articles'],
            search_topics=search_results['search_topics'],
            freshness_desc=search_results['freshness'],
            style=style,
            max_tokens=max_tokens
        )
        
        # Combine results
        tracker.complete('Newsletter generated successfully!')
        
        return {
            **newsletter,
            'articles': search_results['articles'],
            'search_topics': search_results['search_topics'],
            'total_articles': search_results['total_articles'],
            'freshness': search_results['freshness']
        }
        
    except Exception as e:
        logger.error(f"Newsletter generation failed: {e}", exc_info=True)
        return None
