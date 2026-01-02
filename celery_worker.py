#!/usr/bin/env python
"""
Celery worker entry point for ThinkWrapper.

Usage:
    python celery_worker.py worker [options]
    python celery_worker.py beat [options]
    
Examples:
    # Start a worker with 4 concurrent processes
    python celery_worker.py worker --loglevel=info --concurrency=4
    
    # Start the beat scheduler for periodic tasks
    python celery_worker.py beat --loglevel=info
    
    # Start worker with autoscale
    python celery_worker.py worker --loglevel=info --autoscale=10,3
"""
import sys
from app.celery_config import celery

if __name__ == '__main__':
    # Remove script name from arguments
    celery.start(argv=sys.argv[1:] if len(sys.argv) > 1 else ['worker', '--help'])
