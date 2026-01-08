"""
Newsletter content assembly and generation.

This module handles the assembly of newsletter content from articles,
including prompt construction, AI generation, and content parsing.
"""

import logging
from typing import List, Dict, Any, Optional
from .progress_tracker import ProgressTracker, ProgressStage

logger = logging.getLogger(__name__)


class NewsletterBuilder:
    """
    Builds newsletter content from articles using AI.
    
    Handles:
    - Prompt construction from articles
    - AI content generation via Claude
    - Response parsing and structuring
    - Progress reporting
    
    Examples:
        >>> builder = NewsletterBuilder(tracker)
        >>> newsletter = builder.build(
        ...     topic="AI trends",
        ...     articles=article_list,
        ...     search_topics=topics,
        ...     style="professional"
        ... )
    """
    
    def __init__(self, progress_tracker: Optional[ProgressTracker] = None):
        """
        Initialize newsletter builder.
        
        Args:
            progress_tracker: Optional ProgressTracker for progress reporting
        """
        self.tracker = progress_tracker or ProgressTracker()
        self.max_articles_for_prompt = 30  # Limit to avoid token overflow
        self.max_description_length = 500  # Per article description
    
    def build(
        self,
        topic: str,
        articles: List[Dict[str, Any]],
        search_topics: List[str],
        freshness_desc: str,
        style: str = "professional",
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Build newsletter content from articles.
        
        Args:
            topic: Main newsletter topic
            articles: List of article dictionaries
            search_topics: List of topics that were searched
            freshness_desc: Description of time period (e.g., "past 7 days")
            style: Writing style
            max_tokens: Maximum tokens for AI generation
            
        Returns:
            Dictionary containing:
                - subject: Newsletter subject line
                - content: Newsletter body content
                - model: AI model used
                - usage: Token usage statistics
                
        Raises:
            Exception: If content generation fails
        """
        self.tracker.report(
            ProgressStage.GENERATING,
            'Preparing articles for AI...',
            65
        )
        
        # Prepare articles for the prompt
        articles_text = self._format_articles_for_prompt(articles)
        
        # Construct the prompt
        prompt = self._build_prompt(
            topic, articles_text, search_topics, freshness_desc, style
        )
        system_prompt = self._build_system_prompt()
        
        self.tracker.report(
            ProgressStage.GENERATING,
            'Generating newsletter with Claude AI...',
            75
        )
        
        # Generate content with Sonnet for higher quality
        from . import claude_service
        result = claude_service.generate_text(
            prompt=prompt,
            model="claude-sonnet-4-5",  # Use Sonnet for newsletter generation
            max_tokens=max_tokens,
            temperature=0.7,
            system_prompt=system_prompt
        )
        
        if not result:
            raise Exception("Failed to generate newsletter content")
        
        self.tracker.report(
            ProgressStage.GENERATING,
            'Parsing AI response...',
            95
        )
        
        # Parse the response
        subject, body = self._parse_response(result['text'])
        
        return {
            'subject': subject,
            'content': body,
            'model': result['model'],
            'usage': result['usage']
        }
    
    def _format_articles_for_prompt(self, articles: List[Dict[str, Any]]) -> str:
        """
        Format articles into text for the AI prompt.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Formatted articles text
        """
        formatted_articles = []
        
        # Limit number of articles to avoid token overflow
        articles_to_use = articles[:self.max_articles_for_prompt]
        
        for i, article in enumerate(articles_to_use):
            title = self._sanitize_text(article.get('title', ''))
            url = self._sanitize_text(article.get('url', ''))
            description = self._sanitize_text(article.get('description', ''))
            search_topic = article.get('search_topic', 'general')
            
            formatted_articles.append(
                f"Article {i+1}:\n"
                f"Topic: {search_topic}\n"
                f"Title: {title}\n"
                f"URL: {url}\n"
                f"Description: {description}"
            )
        
        return "\n\n".join(formatted_articles)
    
    def _build_prompt(
        self,
        topic: str,
        articles_text: str,
        search_topics: List[str],
        freshness_desc: str,
        style: str
    ) -> str:
        """Build the AI generation prompt with straightforward news delivery tone."""
        return (
            f"Create a newsletter about {topic} using the following real articles.\n\n"
            f"Style: {style}\n"
            f"Time period: Articles from {freshness_desc}\n"
            f"Search topics covered: {', '.join(search_topics)}\n\n"
            f"Real Articles to Reference:\n{articles_text}\n\n"
            f"Structure your response as follows:\n"
            f"1. Start with a clear subject line on the first line (prefix with \"Subject: \")\n"
            f"2. Follow with the newsletter body:\n"
            f"   - Brief opening (2-3 sentences) - no hype, just context\n"
            f"   - 5-7 sections covering the news, organized by theme\n"
            f"   - Each section: state the news/development, provide key details, cite sources\n"
            f"   - Include REAL URLs from the articles (not placeholder URLs)\n"
            f"   - Reference articles by title with their actual URLs\n"
            f"   - Short closing (1-2 sentences)\n\n"
            f"TONE: Straightforward news delivery. Present information clearly without:\n"
            f"- Marketing language ('exciting', 'revolutionary', 'game-changing')\n"
            f"- Excessive enthusiasm or hype\n"
            f"- Overly dramatic framing\n\n"
            f"Instead: \"Here's what happened\", \"New data shows\", \"Company announced\"\n\n"
            f"IMPORTANT: Use only the real URLs provided above. Do not make up or hallucinate any URLs."
        )
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for AI with straightforward news tone."""
        return (
            "You are a professional newsletter writer who delivers news clearly and directly. "
            "Your style is informative and straightforward - no hype, no marketing language, no excessive enthusiasm. "
            "You MUST use only the real article URLs provided - never make up or hallucinate URLs. "
            "Always start with a subject line prefixed with \"Subject: \" on the first line, "
            "followed by the newsletter content with real, verified links from the provided articles."
        )
    
    def _parse_response(self, content: str) -> tuple[str, str]:
        """
        Parse AI response to extract subject and body.
        
        Args:
            content: Raw AI response text
            
        Returns:
            Tuple of (subject, body)
        """
        content = content.strip()
        lines = content.split('\n', 1)
        
        # Extract subject line
        subject = lines[0]
        if subject.lower().startswith('subject:'):
            subject = subject[8:].strip()
        
        # Extract body (everything after the first line)
        body = lines[1].strip() if len(lines) > 1 else ""
        
        return subject, body
    
    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text for use in AI prompts.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text safe for prompts
        """
        if not text:
            return ""
        
        # Remove or escape potentially problematic characters
        sanitized = text.replace('\n', ' ').replace('\r', ' ')
        
        # Remove multiple spaces
        sanitized = ' '.join(sanitized.split())
        
        # Limit length to prevent token overflow
        if len(sanitized) > self.max_description_length:
            sanitized = sanitized[:self.max_description_length] + "..."
        
        return sanitized
