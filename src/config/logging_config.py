"""
Centralized logging configuration for the IBCo Vallejo Console.

Provides structured logging with support for both JSON and text formats.
Integrates with the application settings for easy configuration.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict

from src.config.settings import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs log records as JSON objects for easy parsing by log aggregation tools.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Add custom fields from record
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "extra",
            ]:
                log_data[key] = value

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter for development.

    Provides colored output and clear formatting for console viewing.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with colors."""
        # Get color for log level
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Format message
        log_message = (
            f"{color}{timestamp} - {record.levelname:8s}{reset} - "
            f"{record.name} - {record.getMessage()}"
        )

        # Add exception info if present
        if record.exc_info:
            log_message += "\n" + self.formatException(record.exc_info)

        return log_message


def setup_logging() -> None:
    """
    Configure application-wide logging.

    Sets up logging format, handlers, and log levels based on settings.
    Should be called once at application startup.
    """
    # Get log level from settings
    log_level = getattr(logging, settings.log_level, logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Choose formatter based on settings
    if settings.log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure third-party loggers
    _configure_third_party_loggers()

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured: level={settings.log_level}, format={settings.log_format}"
    )


def _configure_third_party_loggers() -> None:
    """Configure log levels for third-party libraries."""
    # Uvicorn - keep INFO level for server messages
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    # SQLAlchemy - reduce noise unless debugging
    if settings.is_development and settings.log_level == "DEBUG":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)

    # Celery - moderate logging
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("celery.worker").setLevel(logging.INFO)
    logging.getLogger("celery.task").setLevel(logging.INFO)

    # HTTP libraries - reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Other libraries
    logging.getLogger("multipart").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Name of the logger (typically __name__)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context: Any
) -> None:
    """
    Log a message with additional context fields.

    Useful for adding structured data to log messages.

    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **context: Additional context fields

    Example:
        >>> logger = get_logger(__name__)
        >>> log_with_context(
        ...     logger,
        ...     "info",
        ...     "Processing data",
        ...     fiscal_year=2023,
        ...     record_count=1500
        ... )
    """
    log_method = getattr(logger, level.lower())
    extra_dict = {"extra": context} if context else {}

    # Add context as extra fields for JSON formatter
    log_record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "(unknown file)",
        0,
        message,
        (),
        None,
        extra=context,
    )
    logger.handle(log_record)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context to all log messages.

    Useful for adding request IDs, user IDs, or other contextual information
    to all log messages from a particular component.

    Example:
        >>> base_logger = get_logger(__name__)
        >>> logger = LoggerAdapter(base_logger, {"request_id": "abc123"})
        >>> logger.info("Processing request")
        # Output includes request_id in the log record
    """

    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        """Add extra context to log messages."""
        # Merge adapter's extra dict with any extra from the log call
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"].update(self.extra)
        return msg, kwargs


# Convenience function for development debugging
def debug_log_settings() -> None:
    """Log current settings for debugging purposes (development only)."""
    if not settings.is_development:
        return

    logger = get_logger(__name__)
    logger.debug("=" * 50)
    logger.debug("CURRENT SETTINGS:")
    logger.debug(f"  Environment: {settings.environment}")
    logger.debug(f"  Debug: {settings.debug}")
    logger.debug(f"  Log Level: {settings.log_level}")
    logger.debug(f"  Log Format: {settings.log_format}")
    logger.debug(f"  Database URL: {settings.database_url[:30]}...")
    logger.debug(f"  Redis URL: {settings.redis_url}")
    logger.debug("=" * 50)
