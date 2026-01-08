"""
Search orchestration for multi-topic newsletter research.

This module coordinates multi-topic searches across Brave Search API,
managing topic generation, search execution, and result aggregation.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from .progress_tracker import ProgressTracker, ProgressStage

logger = logging.getLogger(__name__)


class SearchResult:
    """Container for a single search result article."""
    
    def __init__(self, title: str, url: str, description: str, search_topic: str = None):
        self.title = title
        self.url = url
        self.description = description
        self.search_topic = search_topic
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'title': self.title,
            'url': self.url,
            'description': self.description,
            'search_topic': self.search_topic
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """Create from dictionary."""
        return cls(
            title=data.get('title', ''),
            url=data.get('url', ''),
            description=data.get('description', ''),
            search_topic=data.get('search_topic')
        )


class SearchOrchestrator:
    """
    Orchestrates multi-topic search operations for newsletter generation.
    
    Handles:
    - Topic seed generation via Claude
    - Multi-topic Brave Search execution
    - Result deduplication and aggregation
    - Progress tracking and reporting
    
    Examples:
        >>> orchestrator = SearchOrchestrator(tracker)
        >>> results = orchestrator.execute_multi_search(
        ...     main_topic="AI trends",
        ...     schedule="weekly",
        ...     num_topics=5
        ... )
    """
    
    def __init__(self, progress_tracker: Optional[ProgressTracker] = None):
        """
        Initialize search orchestrator.
        
        Args:
            progress_tracker: Optional ProgressTracker for reporting progress
        """
        self.tracker = progress_tracker or ProgressTracker()
    
    def execute_multi_search(
        self,
        main_topic: str,
        schedule: str = 'weekly',
        num_topics: int = 5,
        results_per_topic: int = 10
    ) -> Dict[str, Any]:
        """
        Execute multi-topic search orchestration.
        
        This is the main entry point that:
        1. Generates search topic seeds
        2. Searches each topic with date filtering
        3. Aggregates unique results
        
        Args:
            main_topic: Main newsletter topic
            schedule: Newsletter schedule for date filtering
            num_topics: Number of search topics to generate
            results_per_topic: Results to fetch per topic
            
        Returns:
            Dictionary containing:
                - articles: List of unique articles
                - search_topics: List of topics searched
                - freshness: Time period description
                - total_articles: Count of unique articles
                
        Raises:
            Exception: If topic generation or search fails
        """
        # Stage 1: Generate search topics
        self.tracker.report(
            ProgressStage.TOPIC_SEEDING,
            f'Generating search topics for: {main_topic}',
            5
        )
        
        search_topics = self._generate_search_topics(main_topic, num_topics)
        
        if not search_topics:
            raise Exception("Failed to generate search topics")
        
        self.tracker.report(
            ProgressStage.TOPIC_SEEDING,
            f'Generated {len(search_topics)} search topics',
            20
        )
        
        # Stage 2: Execute searches
        freshness, freshness_desc = self._get_freshness_params(schedule)
        
        self.tracker.report(
            ProgressStage.SEARCHING,
            f'Searching articles ({freshness_desc})...',
            25
        )
        
        articles = self._execute_searches(
            search_topics,
            freshness,
            results_per_topic
        )
        
        self.tracker.report(
            ProgressStage.SEARCHING,
            f'Found {len(articles)} unique articles',
            60
        )
        
        return {
            'articles': articles,
            'search_topics': search_topics,
            'freshness': freshness_desc,
            'total_articles': len(articles)
        }
    
    def _generate_search_topics(self, main_topic: str, num_topics: int) -> List[str]:
        """
        Generate search topic seeds using Claude.
        
        Args:
            main_topic: Main newsletter topic
            num_topics: Number of topics to generate
            
        Returns:
            List of search topic strings
        """
        from . import claude_service
        
        topics = claude_service.generate_search_topics(main_topic, num_topics)
        
        if topics:
            logger.info(f"Generated search topics: {topics}")
        else:
            logger.error(f"Failed to generate topics for: {main_topic}")
        
        return topics or []
    
    def _get_freshness_params(self, schedule: str) -> tuple[str, str]:
        """
        Get freshness parameters for the schedule.
        
        Args:
            schedule: Newsletter schedule
            
        Returns:
            Tuple of (freshness_code, freshness_description)
        """
        from .services import get_freshness_from_schedule
        
        freshness = get_freshness_from_schedule(schedule)
        freshness_descriptions = {
            'pd': 'past 24 hours',
            'pw': 'past 7 days',
            'pm': 'past 30 days',
        }
        freshness_desc = freshness_descriptions.get(freshness, 'any time')
        
        return freshness, freshness_desc
    
    def _execute_searches(
        self,
        search_topics: List[str],
        freshness: Optional[str],
        results_per_topic: int
    ) -> List[Dict[str, Any]]:
        """
        Execute web, news, and arXiv searches for each topic and aggregate results.
        
        For each topic, queries Brave Web Search, Brave News Search, and arXiv
        to get comprehensive coverage across general web, news, and academic sources.
        Respects API rate limits with 2.5s delays between requests.
        
        Args:
            search_topics: List of topics to search
            freshness: Time filter parameter (e.g., 'pd', 'pw', 'pm')
            results_per_topic: Results per topic per API
            
        Returns:
            List of unique article dictionaries
        """
        from .services import search_brave, search_arxiv
        
        all_articles = []
        seen_urls = set()
        
        # Calculate total search operations (3 per topic: web + news + arxiv)
        total_searches = len(search_topics) * 3
        search_count = 0
        
        for i, search_topic in enumerate(search_topics):
            # Web Search
            search_count += 1
            progress = 25 + int((search_count / total_searches) * 35)  # 25-60%
            self.tracker.report(
                ProgressStage.SEARCHING,
                f'Web: {search_topic[:35]}...',
                progress
            )
            
            web_results = search_brave(
                query=search_topic,
                count=results_per_topic,
                fallback_to_mock=False,
                freshness=freshness,
                search_type='web'
            )
            
            # Add unique web results
            if web_results.get('success') and web_results.get('results'):
                for article in web_results['results']:
                    url = article.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_articles.append({
                            **article,
                            'search_topic': search_topic,
                            'source_type': 'web'
                        })
            
            # Rate limit before news search (2.5s to avoid 429 errors)
            time.sleep(2.5)
            
            # News Search
            search_count += 1
            progress = 25 + int((search_count / total_searches) * 35)
            self.tracker.report(
                ProgressStage.SEARCHING,
                f'News: {search_topic[:34]}...',
                progress
            )
            
            news_results = search_brave(
                query=search_topic,
                count=results_per_topic,
                fallback_to_mock=False,
                freshness=freshness,
                search_type='news'
            )
            
            # Add unique news results
            if news_results.get('success') and news_results.get('results'):
                for article in news_results['results']:
                    url = article.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_articles.append({
                            **article,
                            'search_topic': search_topic,
                            'source_type': 'news'
                        })
            
            # Rate limit before arXiv search
            time.sleep(2.5)
            
            # arXiv Search
            search_count += 1
            progress = 25 + int((search_count / total_searches) * 35)
            self.tracker.report(
                ProgressStage.SEARCHING,
                f'arXiv: {search_topic[:33]}...',
                progress
            )
            
            arxiv_results = search_arxiv(
                query=search_topic,
                count=results_per_topic,
                freshness=freshness
            )
            
            # Add unique arXiv results
            if arxiv_results.get('success') and arxiv_results.get('results'):
                for article in arxiv_results['results']:
                    url = article.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_articles.append({
                            **article,
                            'search_topic': search_topic,
                            'source_type': 'arxiv'
                        })
            
            # Rate limit before next topic (except after last)
            if i < len(search_topics) - 1:
                logger.debug(f"Rate limiting: waiting 2.5s before next topic")
                time.sleep(2.5)
        
        logger.info(f"Collected {len(all_articles)} unique articles from {len(search_topics)} topics (web + news + arXiv)")
        return all_articles
