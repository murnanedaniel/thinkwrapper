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
                "orchestrator": "claude-3-5-haiku-20241022",
                "researcher": "claude-3-5-haiku-20241022",
                "writer": "claude-3-5-haiku-20241022"
            }
        
        # Production: Opus orchestrates, Sonnet does the work
        return {
            "orchestrator": "claude-3-5-sonnet-20241022",  # Sonnet for orchestration
            "researcher": "claude-3-5-sonnet-20241022",    # Sonnet for research
            "writer": "claude-3-5-sonnet-20241022"         # Sonnet for writing
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
        
        # Build the main prompt for orchestrator
        main_prompt = f"""Create a newsletter about: {topic}

Style: {style}
Time period: Focus on articles from {freshness_desc}
Workspace: {workspace}

YOU ARE AN ORCHESTRATOR. Do NOT do the work yourself. Instead, DELEGATE to subagents:

STEP 1: Delegate to "topic-generator" subagent
- Use the Task tool to invoke the topic-generator
- Tell it to generate 5-7 diverse search queries for "{topic}"
- Wait for it to complete

STEP 2: Delegate to "article-researcher" subagent
- Use the Task tool to invoke the article-researcher
- Give it the search queries from step 1
- Tell it to search for articles and save summaries to {workspace}/articles.txt
- Wait for it to complete

STEP 3: Delegate to "newsletter-writer" subagent
- Use the Task tool to invoke the newsletter-writer
- Tell it to read {workspace}/articles.txt and write the final newsletter to {workspace}/newsletter.txt
- Wait for it to complete

CRITICAL RULES:
- DO NOT use WebSearch, Write, or Read yourself - let the subagents do it
- ONLY use the Task tool to delegate work
- Each subagent has the tools it needs already configured
- Your job is to COORDINATE, not execute"""
        
        log_progress(f"Starting newsletter generation: {topic}")
        log_progress(f"Mode: {'DEBUG (all Haiku)' if self.debug_mode else 'PRODUCTION (Sonnet)'}")
        
        # Create options with subagents
        options = ClaudeAgentOptions(
            model=self.models["orchestrator"],
            allowed_tools=["Task", "Read", "Write", "WebSearch", "WebFetch"],
            agents=self._create_subagents(),
            cwd=workspace,
            permission_mode="acceptEdits"  # Auto-approve file operations
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
                            # Tool being called - log with inputs!
                            tool_name = block.name
                            tool_input = getattr(block, "input", {})
                            
                            # Format tool input for logging
                            if tool_name == "WebSearch":
                                query_str = tool_input.get("query", "")
                                log_progress(f"→ WebSearch: '{query_str}'")
                                logger.info(f"[Tool: WebSearch] Query: {query_str}")
                            elif tool_name == "Write":
                                filepath = tool_input.get("file_path", "")
                                content_preview = str(tool_input.get("content", ""))[:100]
                                log_progress(f"→ Write: {filepath} ({len(str(tool_input.get('content', '')))} chars)")
                                logger.info(f"[Tool: Write] File: {filepath}, Content: {content_preview}...")
                            elif tool_name == "Read":
                                filepath = tool_input.get("file_path", "")
                                log_progress(f"→ Read: {filepath}")
                                logger.info(f"[Tool: Read] File: {filepath}")
                            elif tool_name == "Bash":
                                command = tool_input.get("command", "")
                                log_progress(f"→ Bash: {command}")
                                logger.info(f"[Tool: Bash] Command: {command}")
                            elif tool_name == "Task":
                                agent_name = tool_input.get("agent_name", "")
                                task_prompt = str(tool_input.get("prompt", ""))[:100]
                                log_progress(f"→ Task: {agent_name} - {task_prompt}...")
                                logger.info(f"[Tool: Task] Agent: {agent_name}, Prompt: {task_prompt}...")
                            else:
                                log_progress(f"→ {tool_name}: {str(tool_input)[:100]}")
                                logger.info(f"[Tool: {tool_name}] Input: {tool_input}")
                            
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
