"""
Progress tracking utilities for long-running tasks.

This module provides a centralized way to track and report progress
for newsletter generation and other async operations.
"""

import logging
from typing import Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class ProgressStage(Enum):
    """Enumeration of progress stages for newsletter generation."""
    STARTING = "starting"
    TOPIC_SEEDING = "topic_seeding"
    SEARCHING = "searching"
    GENERATING = "generating"
    COMPLETE = "complete"
    ERROR = "error"


class ProgressTracker:
    """
    Tracks and reports progress for long-running operations.
    
    Provides consistent progress reporting with stage tracking,
    percentage calculation, and callback support.
    
    Examples:
        >>> tracker = ProgressTracker(callback=my_callback)
        >>> tracker.report(ProgressStage.SEARCHING, "Searching articles...", 50)
        >>> with tracker.stage(ProgressStage.GENERATING, "Generating content"):
        ...     # do work
        ...     pass
    """
    
    def __init__(self, callback: Optional[Callable] = None):
        """
        Initialize progress tracker.
        
        Args:
            callback: Optional function called on progress updates.
                     Should accept (stage: str, message: str, percent: int)
        """
        self.callback = callback
        self.current_stage = ProgressStage.STARTING
        self.current_percent = 0
    
    def report(self, stage: ProgressStage, message: str, percent: int):
        """
        Report progress update.
        
        Args:
            stage: Current progress stage
            message: Human-readable progress message
            percent: Progress percentage (0-100)
        """
        self.current_stage = stage
        self.current_percent = percent
        
        # Log the progress
        logger.info(f"[{percent}%] {stage.value}: {message}")
        
        # Call the callback if provided
        if self.callback:
            try:
                self.callback(stage.value, message, percent)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    def stage(self, stage: ProgressStage, start_message: str = None):
        """
        Context manager for tracking a stage.
        
        Args:
            stage: The stage to track
            start_message: Optional message to report at stage start
            
        Returns:
            StageContext for use in with statements
            
        Examples:
            >>> with tracker.stage(ProgressStage.SEARCHING, "Starting search"):
            ...     # do search work
            ...     pass
        """
        return StageContext(self, stage, start_message)
    
    def complete(self, message: str = "Complete"):
        """Mark operation as complete."""
        self.report(ProgressStage.COMPLETE, message, 100)
    
    def error(self, message: str):
        """Mark operation as failed."""
        self.report(ProgressStage.ERROR, message, self.current_percent)


class StageContext:
    """Context manager for tracking a progress stage."""
    
    def __init__(self, tracker: ProgressTracker, stage: ProgressStage, start_message: str = None):
        self.tracker = tracker
        self.stage = stage
        self.start_message = start_message
    
    def __enter__(self):
        if self.start_message:
            # Start percentage based on stage
            start_percent = self._get_stage_start_percent(self.stage)
            self.tracker.report(self.stage, self.start_message, start_percent)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.tracker.error(f"{self.stage.value} failed: {exc_val}")
        return False
    
    def _get_stage_start_percent(self, stage: ProgressStage) -> int:
        """Get typical start percentage for a stage."""
        stage_percents = {
            ProgressStage.STARTING: 0,
            ProgressStage.TOPIC_SEEDING: 5,
            ProgressStage.SEARCHING: 25,
            ProgressStage.GENERATING: 65,
            ProgressStage.COMPLETE: 100,
        }
        return stage_percents.get(stage, 0)


def create_celery_callback(celery_task):
    """
    Create a progress callback for Celery tasks.
    
    Args:
        celery_task: The Celery task instance (bound with @task(bind=True))
        
    Returns:
        Callback function for use with ProgressTracker
        
    Examples:
        >>> @celery.task(bind=True)
        ... def my_task(self):
        ...     callback = create_celery_callback(self)
        ...     tracker = ProgressTracker(callback)
        ...     tracker.report(ProgressStage.SEARCHING, "Searching...", 50)
    """
    def callback(stage: str, message: str, percent: int):
        celery_task.update_state(
            state='PROGRESS',
            meta={
                'stage': stage,
                'message': message,
                'percent': percent
            }
        )
    return callback
