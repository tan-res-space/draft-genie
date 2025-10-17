"""
Logging configuration for Evaluation Service with enhanced error tracking
"""
import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime

from app.core.config import settings

# Try to import enhanced logging
try:
    from libs.python.common.enhanced_logging import (
        setup_enhanced_logging,
        get_enhanced_logger,
    )
    ENHANCED_LOGGING_AVAILABLE = True
except ImportError:
    ENHANCED_LOGGING_AVAILABLE = False


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

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

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging() -> None:
    """Setup logging configuration with enhanced error tracking"""
    # Use enhanced logging if available
    if ENHANCED_LOGGING_AVAILABLE:
        setup_enhanced_logging(
            service_name=settings.app_name,
            environment=settings.environment,
            log_level=settings.log_level,
            include_locals=False,
            json_logs=True,
        )
        return

    # Fallback to basic logging
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    if ENHANCED_LOGGING_AVAILABLE:
        return get_enhanced_logger(name)
    return logging.getLogger(name)

