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
    model: str = "claude-3-5-sonnet-20241022",
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
    model: str = "claude-3-5-sonnet-20241022",
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
