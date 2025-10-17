"""
Logging configuration for the Draft Service

This module provides enhanced logging with comprehensive error tracking.
"""
import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime

from app.core.config import settings

# Try to import enhanced logging, fall back to basic if not available
try:
    from libs.python.common.enhanced_logging import (
        setup_enhanced_logging,
        get_enhanced_logger,
        EnhancedJSONFormatter,
    )
    ENHANCED_LOGGING_AVAILABLE = True
except ImportError:
    ENHANCED_LOGGING_AVAILABLE = False


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.app_name,
            "environment": settings.environment,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)


def setup_logging() -> None:
    """Setup application logging with enhanced error tracking"""
    # Use enhanced logging if available
    if ENHANCED_LOGGING_AVAILABLE:
        setup_enhanced_logging(
            service_name=settings.app_name,
            environment=settings.environment,
            log_level=settings.log_level,
            include_locals=False,  # Set to True for debugging, but be cautious with sensitive data
            json_logs=(settings.log_format.lower() == "json"),
        )
        return

    # Fallback to basic logging
    # Get log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Set formatter based on log format
    if settings.log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("aio_pika").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    if ENHANCED_LOGGING_AVAILABLE:
        return get_enhanced_logger(name)
    return logging.getLogger(name)

