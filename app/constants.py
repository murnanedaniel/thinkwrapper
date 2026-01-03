"""
Application constants and configuration values.

This module centralizes magic numbers and configuration values
to improve maintainability and testability.
"""

# AI Model Configuration
DEFAULT_OPENAI_MODEL = "gpt-4"
DEFAULT_CLAUDE_MODEL = "claude-haiku-4-5"

# Token limits
DEFAULT_MAX_TOKENS = 1024
NEWSLETTER_MAX_TOKENS = 2000
SYNTHESIS_MAX_TOKENS = 800

# Temperature settings
DEFAULT_TEMPERATURE = 0.7
CREATIVE_TEMPERATURE = 1.0

# Search settings
DEFAULT_SEARCH_COUNT = 10
MAX_MOCK_RESULTS = 5

# Newsletter settings
MAX_CONTENT_ITEMS = 10
MIN_CONTENT_ITEMS = 1
MAX_CONTENT_ITEMS_LIMIT = 50

# Valid options
VALID_SCHEDULES = ['daily', 'weekly', 'monthly', 'biweekly']
VALID_DELIVERY_FORMATS = ['html', 'text', 'both']
VALID_STYLES = ['professional', 'casual', 'technical']

# Email settings
DEFAULT_FROM_EMAIL = "newsletter@thinkwrapper.com"

# Retry settings
DEFAULT_RETRY_DELAY = 60
EMAIL_RETRY_DELAY = 30
MAX_NEWSLETTER_RETRIES = 3
MAX_EMAIL_RETRIES = 5

# Timeouts
API_TIMEOUT = 10
SEARCH_TIMEOUT = 10

# Content limits
MAX_TOPIC_LENGTH = 500
MIN_TOPIC_LENGTH = 3
