"""Structlog configuration for the Enterprise IT Support Assistant.

Call configure_logging() once at application startup (in create_app()).
After that, use structlog.get_logger(__name__) anywhere in the codebase.

Output format:
- development: pretty console output for readability
- production: JSON output ingested by Cloud Logging via stdout collection
"""

import logging
import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog for structured JSON logging.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).
            Read from settings.log_level at app startup.
    """
    ...
