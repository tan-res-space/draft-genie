"""
Enhanced logging utilities for comprehensive error tracking and diagnostics.

This module provides enhanced logging capabilities including:
- Full stack trace capture for exceptions
- Request context logging (method, path, headers, body)
- Structured JSON logging for automated analysis
- Sensitive data filtering (passwords, tokens, PII)
- Error severity classification
"""

import json
import logging
import sys
import traceback
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from contextvars import ContextVar

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
request_context_var: ContextVar[Optional[Dict[str, Any]]] = ContextVar("request_context", default=None)


# Sensitive field patterns to redact
SENSITIVE_PATTERNS: Set[str] = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "api-key",
    "authorization",
    "auth",
    "bearer",
    "jwt",
    "session",
    "cookie",
    "csrf",
    "ssn",
    "social_security",
    "credit_card",
    "card_number",
    "cvv",
    "pin",
    "private_key",
    "access_token",
    "refresh_token",
}


def is_sensitive_field(field_name: str) -> bool:
    """Check if a field name contains sensitive information."""
    field_lower = field_name.lower()
    return any(pattern in field_lower for pattern in SENSITIVE_PATTERNS)


def redact_sensitive_data(data: Any, max_depth: int = 10) -> Any:
    """
    Recursively redact sensitive information from data structures.
    
    Args:
        data: Data to redact (dict, list, or primitive)
        max_depth: Maximum recursion depth to prevent infinite loops
        
    Returns:
        Redacted copy of the data
    """
    if max_depth <= 0:
        return "[MAX_DEPTH_REACHED]"
    
    if isinstance(data, dict):
        return {
            key: "[REDACTED]" if is_sensitive_field(key) else redact_sensitive_data(value, max_depth - 1)
            for key, value in data.items()
        }
    elif isinstance(data, (list, tuple)):
        return [redact_sensitive_data(item, max_depth - 1) for item in data]
    elif isinstance(data, str):
        # Redact potential tokens in strings (Bearer tokens, API keys, etc.)
        if len(data) > 20 and re.match(r'^[A-Za-z0-9_\-\.]+$', data):
            # Looks like a token
            return f"{data[:8]}...[REDACTED]"
        return data
    else:
        return data


def extract_request_context(request: Any) -> Dict[str, Any]:
    """
    Extract relevant context from a request object.
    
    Args:
        request: FastAPI Request object or similar
        
    Returns:
        Dictionary containing request context
    """
    context: Dict[str, Any] = {}
    
    try:
        # Extract basic request info
        if hasattr(request, "method"):
            context["method"] = request.method
        if hasattr(request, "url"):
            context["url"] = str(request.url)
            context["path"] = request.url.path if hasattr(request.url, "path") else None
            context["query_params"] = dict(request.url.query_params) if hasattr(request.url, "query_params") else None
        
        # Extract headers (redact sensitive ones)
        if hasattr(request, "headers"):
            headers = dict(request.headers)
            context["headers"] = redact_sensitive_data(headers)
        
        # Extract client info
        if hasattr(request, "client"):
            context["client"] = {
                "host": request.client.host if hasattr(request.client, "host") else None,
                "port": request.client.port if hasattr(request.client, "port") else None,
            }
        
        # Extract user info if available
        if hasattr(request, "user") and request.user:
            context["user_id"] = getattr(request.user, "id", None)
        
        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            context["request_id"] = request_id
            
    except Exception as e:
        context["_extraction_error"] = str(e)
    
    return context


def format_exception_details(exc: Exception, include_locals: bool = False) -> Dict[str, Any]:
    """
    Format exception details for logging.
    
    Args:
        exc: Exception to format
        include_locals: Whether to include local variables (use with caution)
        
    Returns:
        Dictionary containing exception details
    """
    exc_type = type(exc).__name__
    exc_module = type(exc).__module__
    
    details: Dict[str, Any] = {
        "type": exc_type,
        "module": exc_module,
        "message": str(exc),
        "args": exc.args if exc.args else None,
    }
    
    # Extract full traceback
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    details["traceback"] = "".join(tb_lines)
    
    # Extract structured stack frames
    stack_frames: List[Dict[str, Any]] = []
    tb = exc.__traceback__
    while tb is not None:
        frame = tb.tb_frame
        frame_info = {
            "file": frame.f_code.co_filename,
            "function": frame.f_code.co_name,
            "line_number": tb.tb_lineno,
            "code_context": traceback.extract_tb(tb, limit=1)[0].line if traceback.extract_tb(tb, limit=1) else None,
        }
        
        # Optionally include local variables (redacted)
        if include_locals:
            frame_info["locals"] = redact_sensitive_data(dict(frame.f_locals))
        
        stack_frames.append(frame_info)
        tb = tb.tb_next
    
    details["stack_frames"] = stack_frames
    
    # Add exception attributes if any
    exc_attrs = {k: v for k, v in vars(exc).items() if not k.startswith("_")}
    if exc_attrs:
        details["attributes"] = redact_sensitive_data(exc_attrs)
    
    return details


class EnhancedJSONFormatter(logging.Formatter):
    """
    Enhanced JSON formatter for structured logging with comprehensive error details.
    
    This formatter produces machine-readable JSON logs suitable for automated analysis.
    """
    
    def __init__(
        self,
        service_name: str,
        environment: str = "development",
        include_locals: bool = False,
    ):
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.include_locals = include_locals
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log data
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "severity": self._map_severity(record.levelname),
            "service": self.service_name,
            "environment": self.environment,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line_number": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
            "thread_name": record.threadName,
        }
        
        # Add request context if available
        request_context = request_context_var.get()
        if request_context:
            log_data["request"] = request_context
        
        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        # Add exception information if present
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            if exc_value:
                log_data["error"] = format_exception_details(exc_value, self.include_locals)
                log_data["error_type"] = "unhandled_exception"
        
        # Add extra fields from record
        if hasattr(record, "extra_data"):
            extra = redact_sensitive_data(record.extra_data)
            log_data["extra"] = extra
        
        # Add custom fields passed via extra parameter
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info",
                "extra_data",
            ]:
                log_data[key] = redact_sensitive_data(value)
        
        # Add error classification for automated analysis
        if record.levelno >= logging.ERROR:
            log_data["requires_investigation"] = True
            log_data["alert_priority"] = "high" if record.levelno >= logging.CRITICAL else "medium"
        
        return json.dumps(log_data, default=str, ensure_ascii=False)
    
    def _map_severity(self, level: str) -> str:
        """Map Python log level to standard severity."""
        mapping = {
            "DEBUG": "DEBUG",
            "INFO": "INFO",
            "WARNING": "WARNING",
            "ERROR": "ERROR",
            "CRITICAL": "CRITICAL",
        }
        return mapping.get(level, "INFO")


def setup_enhanced_logging(
    service_name: str,
    environment: str = "development",
    log_level: str = "INFO",
    include_locals: bool = False,
    json_logs: bool = True,
) -> None:
    """
    Setup enhanced logging configuration.
    
    Args:
        service_name: Name of the service
        environment: Environment (development, staging, production)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        include_locals: Whether to include local variables in stack traces
        json_logs: Whether to output logs in JSON format
    """
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter
    if json_logs:
        formatter = EnhancedJSONFormatter(
            service_name=service_name,
            environment=environment,
            include_locals=include_locals,
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("aio_pika").setLevel(logging.WARNING)


def get_enhanced_logger(name: str) -> logging.Logger:
    """Get an enhanced logger instance."""
    return logging.getLogger(name)

