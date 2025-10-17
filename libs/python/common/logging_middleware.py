"""
FastAPI middleware for comprehensive request/response logging and error tracking.

This middleware captures:
- Request details (method, path, headers, body)
- Response details (status code, headers)
- Request duration
- Errors and exceptions with full stack traces
"""

import json
import logging
import time
import uuid
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .enhanced_logging import (
    request_id_var,
    request_context_var,
    extract_request_context,
    format_exception_details,
    redact_sensitive_data,
)

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all requests and responses with comprehensive error tracking.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        log_request_body: bool = True,
        log_response_body: bool = False,
        max_body_size: int = 10000,  # Maximum body size to log (in bytes)
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate or extract request ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Extract request context
        context = extract_request_context(request)
        request_context_var.set(context)
        
        # Start timing
        start_time = time.time()
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        response: Optional[Response] = None
        error: Optional[Exception] = None
        
        try:
            response = await call_next(request)
            
            # Log response
            await self._log_response(request, response, request_id, start_time)
            
            # Add request ID to response headers
            response.headers["x-request-id"] = request_id
            
            return response
            
        except Exception as exc:
            error = exc
            # Log error with full details
            await self._log_error(request, exc, request_id, start_time)
            
            # Create error response
            error_response = self._create_error_response(exc, request_id)
            error_response.headers["x-request-id"] = request_id
            
            return error_response
    
    async def _log_request(self, request: Request, request_id: str) -> None:
        """Log incoming request details."""
        log_data = {
            "event": "request_received",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.url.query_params) if request.url.query_params else None,
            "headers": redact_sensitive_data(dict(request.headers)),
            "client": {
                "host": request.client.host if request.client else None,
                "port": request.client.port if request.client else None,
            },
        }
        
        # Log request body if enabled
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await self._get_request_body(request)
                if body:
                    log_data["body"] = redact_sensitive_data(body)
            except Exception as e:
                log_data["body_error"] = str(e)
        
        logger.info(
            f"{request.method} {request.url.path}",
            extra={"extra_data": log_data}
        )
    
    async def _log_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        start_time: float,
    ) -> None:
        """Log response details."""
        duration_ms = (time.time() - start_time) * 1000
        
        log_data = {
            "event": "request_completed",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "response_headers": redact_sensitive_data(dict(response.headers)),
        }
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = logging.ERROR
            log_data["error_type"] = "server_error"
        elif response.status_code >= 400:
            log_level = logging.WARNING
            log_data["error_type"] = "client_error"
        else:
            log_level = logging.INFO
        
        logger.log(
            log_level,
            f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)",
            extra={"extra_data": log_data}
        )
    
    async def _log_error(
        self,
        request: Request,
        error: Exception,
        request_id: str,
        start_time: float,
    ) -> None:
        """Log error with full stack trace and context."""
        duration_ms = (time.time() - start_time) * 1000
        
        # Format exception details
        error_details = format_exception_details(error, include_locals=False)
        
        log_data = {
            "event": "request_failed",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "duration_ms": round(duration_ms, 2),
            "error": error_details,
            "request_context": extract_request_context(request),
        }
        
        logger.error(
            f"Unhandled exception in {request.method} {request.url.path}: {type(error).__name__}: {str(error)}",
            exc_info=error,
            extra={"extra_data": log_data}
        )
    
    async def _get_request_body(self, request: Request) -> Optional[dict]:
        """Safely extract request body."""
        try:
            # Check content type
            content_type = request.headers.get("content-type", "")
            
            if "application/json" in content_type:
                # Get body bytes
                body_bytes = await request.body()
                
                # Check size
                if len(body_bytes) > self.max_body_size:
                    return {"_truncated": f"Body too large ({len(body_bytes)} bytes)"}
                
                # Parse JSON
                if body_bytes:
                    return json.loads(body_bytes)
            
            return None
            
        except Exception as e:
            return {"_error": f"Failed to parse body: {str(e)}"}
    
    def _create_error_response(self, error: Exception, request_id: str) -> JSONResponse:
        """Create standardized error response."""
        # Determine status code
        status_code = getattr(error, "status_code", 500)
        
        # Create error response
        error_response = {
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "request_id": request_id,
                "timestamp": time.time(),
            }
        }
        
        # Add details if available
        if hasattr(error, "detail"):
            error_response["error"]["detail"] = error.detail
        
        return JSONResponse(
            status_code=status_code,
            content=error_response,
        )


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Lightweight middleware specifically for tracking 5xx errors.
    
    This middleware ensures all server errors are logged with full context,
    even if they occur outside the normal request processing flow.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track and log server errors."""
        try:
            response = await call_next(request)
            
            # Log 5xx responses
            if response.status_code >= 500:
                logger.error(
                    f"Server error: {request.method} {request.url.path} returned {response.status_code}",
                    extra={
                        "extra_data": {
                            "event": "server_error_response",
                            "status_code": response.status_code,
                            "method": request.method,
                            "path": request.url.path,
                            "request_id": request_id_var.get(),
                        }
                    }
                )
            
            return response
            
        except Exception as exc:
            # Log unhandled exception
            logger.critical(
                f"Critical error in request processing: {type(exc).__name__}: {str(exc)}",
                exc_info=exc,
                extra={
                    "extra_data": {
                        "event": "critical_error",
                        "method": request.method,
                        "path": request.url.path,
                        "request_id": request_id_var.get(),
                        "error": format_exception_details(exc),
                    }
                }
            )
            raise

