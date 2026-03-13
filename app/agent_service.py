"""
Agent-based newsletter generation using Claude Agent SDK.

Replaces: claude_service.py, search_orchestrator.py, newsletter_builder.py

Uses the Claude Agent SDK with programmatic subagents for multi-model workflow:
- Opus/Sonnet for orchestration
- Sonnet for research tasks  
- Sonnet for newsletter writing
- Haiku for mundane tasks (debug mode: all Haiku)
"""
import asyncio
import os
import logging
from typing import Optional, Dict, Any, Callable
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition, AssistantMessage, ResultMessage
from app.services import get_freshness_from_schedule

logger = logging.getLogger(__name__)


class NewsletterAgentService:
    """Newsletter generation using Claude Agent SDK with subagents."""
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialize the newsletter agent service.
        
        Args:
            debug_mode: If True, use Haiku for all models (fast/cheap debugging)
        """
        self.debug_mode = debug_mode
        self.models = self._get_model_config()
    
    def _get_model_config(self) -> Dict[str, str]:
        """
        Get model configuration based on debug mode.
        
        Returns:
            Dictionary mapping role to model name
        """
        if self.debug_mode:
            return {
                "orchestrator": "claude-haiku-4-5-20251001",
                "researcher": "claude-haiku-4-5-20251001",
                "writer": "claude-haiku-4-5-20251001",
            }

        return {
            "orchestrator": "claude-sonnet-4-6",
            "researcher": "claude-sonnet-4-6",
            "writer": "claude-sonnet-4-6",
        }
    
    def _create_subagents(self) -> Dict[str, AgentDefinition]:
        """
        Create subagent definitions with model routing.
        
        Returns:
            Dictionary of subagent definitions
        """
        return {
            "topic-generator": AgentDefinition(
                description="Generate diverse search topics for newsletter research. Use when you need to create search queries covering different angles of a topic.",
                prompt="""You are a search topic generator. Given a main newsletter topic, 
                generate 5-7 specific, diverse search queries that cover different angles. 
                Make queries specific enough to find relevant articles. Output just the queries, 
                one per line.""",
                tools=["Write"],  # Can write topics to a file
                model=self.models["researcher"]
            ),
            "article-researcher": AgentDefinition(
                description="Search the web and arXiv for articles, fetch full content, and summarize key points. Use for gathering and analyzing research.",
                prompt="""You are a research agent. Search for articles on given topics using WebSearch 
                for general content and WebFetch to read full articles when needed. For academic topics, 
                note that arXiv papers can be searched too (mention this in your findings).
                
                Summarize each article in 2-3 sentences covering:
                - Main point or finding
                - Why it's relevant
                - Source URL (must be real, from search results)
                
                Save your summaries to /tmp/newsletter_research/articles.txt with this format:
                ARTICLE: [title]
                URL: [url]
                SUMMARY: [your 2-3 sentence summary]
                ---""",
                tools=["WebSearch", "WebFetch", "Read", "Write"],
                model=self.models["researcher"]
            ),
            "newsletter-writer": AgentDefinition(
                description="Compose polished newsletter content from research summaries. Use after research is complete to write the final newsletter.",
                prompt="""You are a professional newsletter writer. Read the research summaries 
                and compose an engaging newsletter.
                
                Format:
                - Start with Subject: [compelling subject line]
                - Brief introduction (2-3 sentences)
                - 5-7 sections covering different aspects
                - Each section: state the news, provide key details, cite sources with real URLs
                - Brief conclusion
                
                Tone: Straightforward news delivery. No hype, no marketing language. 
                Just clear "here's what happened" reporting.
                
                CRITICAL: Use ONLY the real URLs from the research summaries. Never make up or hallucinate URLs.""",
                tools=["Read", "Write"],
                model=self.models["writer"]
            )
        }
    
    async def generate_newsletter(
        self,
        topic: str,
        schedule: str = "weekly",
        style: str = "professional",
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Generate newsletter using Claude Agent SDK with subagents.
        
        This uses the Claude Agent SDK's built-in agent orchestration with
        programmatic subagents for multi-model workflow.
        
        Args:
            topic: Main newsletter topic
            schedule: Newsletter schedule for date filtering (daily, weekly, etc.)
            style: Writing style
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with newsletter content and metadata
            
        Raises:
            Exception: If generation fails
        """
        # Create workspace directory
        workspace = "/tmp/newsletter_research"
        os.makedirs(workspace, exist_ok=True)
        
        # Get freshness parameter
        freshness = get_freshness_from_schedule(schedule)
        freshness_desc = {
            'pd': 'past 24 hours',
            'pw': 'past 7 days', 
            'pm': 'past 30 days'
        }.get(freshness, 'any time')
        
        def log_progress(msg: str):
            """Log and emit progress."""
            logger.info(f"[Agent] {msg}")
            print(f"[Agent] {msg}")
            if progress_callback:
                progress_callback(msg)
        
        # Build a single-agent prompt — Claude does everything itself
        main_prompt = f"""You are a professional newsletter writer. Create a complete newsletter about: {topic}

Style: {style}
Time period: Focus on news from {freshness_desc}

STEPS (do all of these yourself):
1. Use WebSearch to find 6-8 recent, relevant articles about "{topic}" and subtopics
2. Use WebFetch to skim 2-3 of the most promising articles for details
3. Write the final newsletter to {workspace}/newsletter.txt in this exact format:
   - First line: Subject: [compelling subject line]
   - Blank line
   - Body: 5-7 sections, each covering one story/theme
   - Each section: headline, 2-3 sentence summary, source URL (real URLs only)
   - Brief closing paragraph

TONE: Straightforward news delivery — no hype, no marketing language.
CRITICAL: Only use real URLs from your search results. Never hallucinate URLs."""

        log_progress(f"Starting newsletter generation: {topic}")
        log_progress(f"Mode: {'DEBUG (all Haiku)' if self.debug_mode else 'PRODUCTION (Sonnet)'}")

        options = ClaudeAgentOptions(
            model=self.models["orchestrator"],
            allowed_tools=["WebSearch", "WebFetch", "Write"],
            cwd=workspace,
            permission_mode="bypassPermissions",
        )
        
        # Track the conversation and timing
        import time
        start_time = time.time()
        result_content = None
        
        try:
            # Run the agent
            log_progress("Orchestrator agent starting...")
            log_progress(f"Timestamp: {time.strftime('%H:%M:%S')}")
            
            async for message in query(prompt=main_prompt, options=options):
                # Handle different message types properly per SDK docs
                if isinstance(message, AssistantMessage):
                    # AssistantMessage contains Claude's reasoning and tool calls
                    for block in message.content:
                        if hasattr(block, "text"):
                            # Claude's reasoning text
                            text = block.text
                            log_progress(f"Claude: {text[:150]}...")
                            logger.info(f"[Agent Reasoning] {text}")
                        elif hasattr(block, "name"):
                            tool_name = block.name
                            tool_input = getattr(block, "input", {})
                            if tool_name == "WebSearch":
                                q = tool_input.get("query", "")
                                log_progress(f"Searching: {q}")
                            elif tool_name == "WebFetch":
                                url = tool_input.get("url", "")
                                log_progress(f"Reading article: {url[:70]}...")
                            elif tool_name == "Write":
                                log_progress("Writing newsletter...")
                            # skip internal tools: TodoWrite, TodoRead, Read, Bash, etc.
                            
                elif isinstance(message, ResultMessage):
                    # Final result message with timing
                    elapsed = time.time() - start_time
                    log_progress(f"✓ Complete: {message.subtype} (took {elapsed:.1f}s)")
                    logger.info(f"[Result] {message.subtype} - Duration: {elapsed:.1f}s")
                    result_content = message
                    
                else:
                    # Other message types (system, tool results, etc.)
                    msg_type = type(message).__name__
                    logger.debug(f"[Message] {msg_type}: {message}")
            
            # Parse the result
            if result_content:
                return self._parse_newsletter_result(result_content, workspace)
            else:
                # Try to read from workspace if no result returned
                log_progress("No direct result, checking workspace...")
                return self._read_newsletter_from_workspace(workspace)
                
        except Exception as e:
            logger.error(f"Newsletter generation failed: {e}", exc_info=True)
            log_progress(f"Error: {e}")
            raise
    
    def _parse_newsletter_result(self, result: Any, workspace: str) -> Dict[str, Any]:
        """
        Parse newsletter result from agent output.
        
        Args:
            result: Result from agent (ResultMessage or string)
            workspace: Workspace directory
            
        Returns:
            Parsed newsletter dictionary
        """
        # Try to read the newsletter file first (most reliable)
        newsletter_file = os.path.join(workspace, 'newsletter.txt')
        if os.path.exists(newsletter_file):
            with open(newsletter_file, 'r') as f:
                content = f.read()
        elif isinstance(result, str):
            content = result
        else:
            # Result is a ResultMessage or other object
            content = str(result)
        
        # Try to extract subject and body
        lines = content.split('\n', 1)
        subject = lines[0]
        
        # Clean subject line
        if subject.lower().startswith('subject:'):
            subject = subject[8:].strip()
        
        body = lines[1].strip() if len(lines) > 1 else content
        
        # Try to read articles from workspace for metadata
        articles = []
        try:
            articles_file = os.path.join(workspace, 'articles.txt')
            if os.path.exists(articles_file):
                with open(articles_file, 'r') as f:
                    articles_text = f.read()
                    # Basic parsing of articles
                    article_blocks = articles_text.split('---')
                    for block in article_blocks:
                        if 'ARTICLE:' in block and 'URL:' in block:
                            articles.append({'raw': block.strip()})
        except Exception as e:
            logger.warning(f"Could not read articles file: {e}")
        
        return {
            'subject': subject,
            'content': body,
            'articles': articles,
            'total_articles': len(articles),
            'model': self.models['orchestrator'],
            'mode': 'debug' if self.debug_mode else 'production'
        }
    
    def _read_newsletter_from_workspace(self, workspace: str) -> Dict[str, Any]:
        """
        Try to read newsletter from workspace files.
        
        Args:
            workspace: Workspace directory
            
        Returns:
            Newsletter dictionary
            
        Raises:
            Exception: If newsletter cannot be found
        """
        # Check for common output files
        possible_files = ['newsletter.txt', 'newsletter.md', 'output.txt']
        
        for filename in possible_files:
            filepath = os.path.join(workspace, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    return self._parse_newsletter_result(content, workspace)
        
        raise Exception("Newsletter generation completed but no output file found")


# Sync wrapper for Celery tasks
def generate_newsletter_sync(
    topic: str,
    schedule: str = "weekly",
    style: str = "professional",
    debug_mode: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for newsletter generation.
    
    Args:
        topic: Newsletter topic
        schedule: Newsletter schedule  
        style: Writing style
        debug_mode: Use all Haiku models if True
        progress_callback: Progress callback function
        
    Returns:
        Newsletter dictionary
    """
    service = NewsletterAgentService(debug_mode=debug_mode)
    return asyncio.run(
        service.generate_newsletter(
            topic=topic,
            schedule=schedule,
            style=style,
            progress_callback=progress_callback
        )
    )
