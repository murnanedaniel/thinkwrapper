"""
API Utilities Module

Provides standardized response formatting and input validation
for consistent API behavior across all endpoints.
"""

from functools import wraps
from flask import jsonify, request
from typing import Any, Dict, Optional, Tuple, Callable
import re

from .constants import MAX_TOPIC_LENGTH, MIN_TOPIC_LENGTH


class APIResponse:
    """Standardized API response builder."""

    @staticmethod
    def success(
        data: Any = None,
        message: Optional[str] = None,
        status_code: int = 200
    ) -> Tuple[Dict, int]:
        """
        Create a successful API response.

        Args:
            data: Response payload
            message: Optional success message
            status_code: HTTP status code (default 200)

        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {"success": True}
        if message:
            response["message"] = message
        if data is not None:
            response["data"] = data
        return jsonify(response), status_code

    @staticmethod
    def error(
        error: str,
        details: Optional[str] = None,
        status_code: int = 400
    ) -> Tuple[Dict, int]:
        """
        Create an error API response.

        Args:
            error: Error message
            details: Optional error details
            status_code: HTTP status code (default 400)

        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {"success": False, "error": error}
        if details:
            response["details"] = details
        return jsonify(response), status_code

    @staticmethod
    def processing(
        task_id: str,
        message: str = "Task is being processed"
    ) -> Tuple[Dict, int]:
        """
        Create a processing/async response.

        Args:
            task_id: ID of the async task
            message: Processing status message

        Returns:
            Tuple of (response_dict, 202)
        """
        return jsonify({
            "success": True,
            "status": "processing",
            "task_id": task_id,
            "message": message
        }), 202


class InputValidator:
    """Input validation utilities."""

    @staticmethod
    def validate_topic(topic: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate a newsletter topic.

        Args:
            topic: The topic string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not topic:
            return False, "Topic is required"

        topic = topic.strip()

        if len(topic) < MIN_TOPIC_LENGTH:
            return False, f"Topic must be at least {MIN_TOPIC_LENGTH} characters"

        if len(topic) > MAX_TOPIC_LENGTH:
            return False, f"Topic must be at most {MAX_TOPIC_LENGTH} characters"

        # Check for potentially malicious content
        if InputValidator._contains_injection_patterns(topic):
            return False, "Topic contains invalid characters"

        return True, None

    @staticmethod
    def validate_email(email: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate an email address.

        Args:
            email: The email string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"

        email = email.strip()

        # Basic email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email format"

        if len(email) > 254:
            return False, "Email address is too long"

        return True, None

    @staticmethod
    def validate_style(style: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate a writing style.

        Args:
            style: The style string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        from .constants import VALID_STYLES

        if not style:
            return True, None  # Style is optional, default will be used

        if style.lower() not in VALID_STYLES:
            return False, f"Invalid style. Must be one of: {', '.join(VALID_STYLES)}"

        return True, None

    @staticmethod
    def validate_format(format_type: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate output format.

        Args:
            format_type: The format string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        from .constants import VALID_DELIVERY_FORMATS

        if not format_type:
            return True, None  # Format is optional, default will be used

        if format_type.lower() not in VALID_DELIVERY_FORMATS:
            return False, f"Invalid format. Must be one of: {', '.join(VALID_DELIVERY_FORMATS)}"

        return True, None

    @staticmethod
    def _contains_injection_patterns(text: str) -> bool:
        """
        Check for common injection patterns.

        Args:
            text: The text to check

        Returns:
            True if injection patterns found, False otherwise
        """
        # Check for script injection
        injection_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
            r'<embed',
        ]

        text_lower = text.lower()
        for pattern in injection_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    @staticmethod
    def sanitize_string(text: str) -> str:
        """
        Sanitize a string by removing potentially harmful content.

        Args:
            text: The text to sanitize

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Strip leading/trailing whitespace
        text = text.strip()

        # Remove null bytes
        text = text.replace('\x00', '')

        # Limit consecutive whitespace
        text = re.sub(r'\s+', ' ', text)

        return text


def require_json(f: Callable) -> Callable:
    """
    Decorator to require JSON body in request.

    Usage:
        @require_json
        def my_endpoint():
            data = request.json
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return APIResponse.error(
                "Request must be JSON",
                status_code=415
            )
        if not request.json:
            return APIResponse.error(
                "Request body cannot be empty",
                status_code=400
            )
        return f(*args, **kwargs)
    return decorated_function
