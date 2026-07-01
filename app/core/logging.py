"""Structlog configuration for the Enterprise IT Support Assistant.

Call configure_logging() once at application startup (in create_app()).
After that, use structlog.get_logger(__name__) anywhere in the codebase.

Output format:
- development: pretty console output for readability
- production: JSON output ingested by Cloud Logging via stdout collection
"""

import logging

import structlog


def configure_logging(log_level: str = "INFO", app_env: str = "development") -> None:
    """Configure structlog for structured logging.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).
            Read from settings.log_level at app startup.
        app_env: Application environment. Controls output format:
            development → ConsoleRenderer, production → JSONRenderer.
    """
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    renderer = (
        structlog.dev.ConsoleRenderer()
        if app_env == "development"
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format="%(message)s", level=log_level)
