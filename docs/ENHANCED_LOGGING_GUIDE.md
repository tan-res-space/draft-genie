# Enhanced Logging and Error Tracking Guide

## Overview

The DraftGenie platform now includes comprehensive enhanced logging capabilities designed to capture detailed error information for production troubleshooting and automated error analysis.

## Key Features

### 1. **Comprehensive Error Tracking**
- Full stack traces for all unhandled exceptions
- Structured stack frame information (file, function, line number)
- Request context capture (method, path, headers, body)
- Response tracking (status codes, duration)

### 2. **Automated Analysis Ready**
- Structured JSON logging format
- Machine-readable error metadata
- Severity classification (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Alert priority indicators (high, medium, low)
- Investigation flags for automated triage

### 3. **Security & Privacy**
- Automatic redaction of sensitive data (passwords, tokens, API keys, PII)
- Configurable field patterns for sensitive information
- Safe handling of authentication headers
- Body size limits to prevent log flooding

### 4. **Performance Monitoring**
- Request duration tracking
- Response size monitoring
- Request/response correlation via request IDs
- Performance metrics for automated analysis

## Architecture

### Python Services (FastAPI)

#### Components

1. **Enhanced Logging Module** (`libs/python/common/enhanced_logging.py`)
   - `EnhancedJSONFormatter`: Structured JSON log formatter
   - `setup_enhanced_logging()`: Configure logging system
   - `format_exception_details()`: Extract comprehensive error information
   - `redact_sensitive_data()`: Remove sensitive information from logs

2. **Logging Middleware** (`libs/python/common/logging_middleware.py`)
   - `RequestLoggingMiddleware`: Log all requests/responses
   - `ErrorTrackingMiddleware`: Track 5xx errors specifically

#### Services Using Enhanced Logging
- Draft Service
- RAG Service
- Evaluation Service

### TypeScript Services (NestJS)

#### Components

1. **Global Exception Filter** (`libs/common/src/filters/global-exception.filter.ts`)
   - Catches all unhandled exceptions
   - Logs comprehensive error details
   - Returns standardized error responses

2. **Logging Interceptor** (`libs/common/src/interceptors/logging.interceptor.ts`)
   - Logs all incoming requests
   - Tracks request/response lifecycle
   - Monitors performance metrics

#### Services Using Enhanced Logging
- API Gateway
- Speaker Service

## Log Format

### Structured JSON Format

All logs are output in structured JSON format suitable for automated parsing:

```json
{
  "timestamp": "2025-10-17T10:30:45.123Z",
  "level": "ERROR",
  "severity": "ERROR",
  "service": "draft-service",
  "environment": "production",
  "logger": "app.main",
  "message": "Unhandled exception: ValueError: Invalid draft ID",
  "module": "main",
  "function": "create_draft",
  "line_number": 145,
  "process_id": 12345,
  "thread_id": 67890,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "request": {
    "method": "POST",
    "path": "/api/v1/drafts",
    "url": "http://api.example.com/api/v1/drafts",
    "query": {},
    "headers": {
      "content-type": "application/json",
      "authorization": "[REDACTED]",
      "x-request-id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "body": {
      "speaker_id": "123e4567-e89b-12d3-a456-426614174000",
      "content": "Draft content here"
    },
    "client": {
      "host": "192.168.1.100",
      "port": 54321
    }
  },
  "error": {
    "type": "ValueError",
    "module": "builtins",
    "message": "Invalid draft ID",
    "traceback": "Traceback (most recent call last):\n  File ...",
    "stack_frames": [
      {
        "file": "/app/services/draft_service.py",
        "function": "create_draft",
        "line_number": 145,
        "code_context": "draft = Draft(id=draft_id)"
      },
      {
        "file": "/app/repositories/draft_repository.py",
        "function": "save",
        "line_number": 67,
        "code_context": "self.db.save(draft)"
      }
    ]
  },
  "requires_investigation": true,
  "alert_priority": "high"
}
```

### Log Levels and Severity

| Level | Severity | Use Case | Alert Priority |
|-------|----------|----------|----------------|
| DEBUG | DEBUG | Development debugging | - |
| INFO | INFO | Normal operations | - |
| WARNING | WARNING | Client errors (4xx) | medium |
| ERROR | ERROR | Server errors (5xx) | high |
| CRITICAL | CRITICAL | Critical system failures | high |

## Configuration

### Python Services

#### Environment Variables

```bash
# Logging configuration
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json             # json or text
ENVIRONMENT=production      # development, staging, production
```

#### Code Configuration

```python
from libs.python.common.enhanced_logging import setup_enhanced_logging

# Setup enhanced logging
setup_enhanced_logging(
    service_name="my-service",
    environment="production",
    log_level="INFO",
    include_locals=False,  # Set to True for debugging (caution: may expose sensitive data)
    json_logs=True,
)
```

#### Middleware Configuration

```python
from libs.python.common.logging_middleware import (
    RequestLoggingMiddleware,
    ErrorTrackingMiddleware,
)

# Add to FastAPI app
app.add_middleware(ErrorTrackingMiddleware)
app.add_middleware(
    RequestLoggingMiddleware,
    log_request_body=True,      # Log request bodies
    log_response_body=False,    # Don't log response bodies (can be large)
    max_body_size=10000,        # Maximum body size to log (bytes)
)
```

### TypeScript Services

#### Code Configuration

```typescript
import { 
  GlobalExceptionFilter,
  LoggingInterceptor,
} from '@draft-genie/common';

// In main.ts bootstrap function
app.useGlobalFilters(new GlobalExceptionFilter());
app.useGlobalInterceptors(
  new LoggingInterceptor(
    true,    // logRequestBody
    false,   // logResponseBody
    10000,   // maxBodySize
  )
);
```

## Sensitive Data Protection

### Automatically Redacted Fields

The following field patterns are automatically redacted from logs:

- `password`, `passwd`, `pwd`
- `secret`, `token`, `api_key`, `apikey`
- `authorization`, `auth`, `bearer`, `jwt`
- `session`, `cookie`, `csrf`
- `ssn`, `social_security`
- `credit_card`, `card_number`, `cvv`, `pin`
- `private_key`, `access_token`, `refresh_token`

### Example Redaction

**Original:**
```json
{
  "username": "john.doe",
  "password": "super_secret_123",
  "api_key": "sk_live_abc123xyz789"
}
```

**Logged:**
```json
{
  "username": "john.doe",
  "password": "[REDACTED]",
  "api_key": "[REDACTED]"
}
```

## Request Tracking

### Request ID Correlation

Every request is assigned a unique request ID that flows through the entire request lifecycle:

1. **Generation**: Request ID is generated or extracted from `X-Request-ID` header
2. **Propagation**: Request ID is added to all log entries for that request
3. **Response**: Request ID is returned in response headers
4. **Tracing**: Use request ID to trace a request across all services

### Example Request Flow

```
Client Request → API Gateway → Draft Service → Database
     ↓                ↓              ↓             ↓
Request ID:    550e8400-e29b-41d4-a716-446655440000
```

All logs for this request will include the same `request_id`, enabling easy correlation.

## Automated Error Analysis

### Log Query Examples

#### Find All Server Errors (5xx)

```bash
# Using jq to filter JSON logs
cat logs/application.log | jq 'select(.level == "ERROR" and .requires_investigation == true)'
```

#### Find Errors by Request ID

```bash
cat logs/application.log | jq 'select(.request_id == "550e8400-e29b-41d4-a716-446655440000")'
```

#### Find High Priority Alerts

```bash
cat logs/application.log | jq 'select(.alert_priority == "high")'
```

#### Group Errors by Type

```bash
cat logs/application.log | jq -r 'select(.error) | .error.type' | sort | uniq -c | sort -rn
```

## Best Practices

### 1. **Use Appropriate Log Levels**
```python
logger.debug("Detailed debugging information")
logger.info("Normal operation completed")
logger.warning("Unexpected but handled situation")
logger.error("Error that needs investigation", exc_info=True)
logger.critical("Critical system failure", exc_info=True)
```

### 2. **Include Context in Log Messages**
```python
logger.error(
    f"Failed to create draft for speaker {speaker_id}",
    extra={
        "extra_data": {
            "speaker_id": speaker_id,
            "draft_type": draft_type,
            "error_code": "DRAFT_001",
        }
    }
)
```

### 3. **Always Use exc_info for Exceptions**
```python
try:
    process_draft(draft_id)
except Exception as e:
    logger.error(f"Draft processing failed: {e}", exc_info=True)
    raise
```

### 4. **Don't Log Sensitive Data Manually**
```python
# ❌ BAD
logger.info(f"User logged in with password: {password}")

# ✅ GOOD
logger.info(f"User logged in", extra={"extra_data": {"user_id": user_id}})
```

## Monitoring and Alerting

### Recommended Monitoring Queries

1. **Error Rate**: Count of ERROR/CRITICAL logs per minute
2. **High Priority Alerts**: Count of logs with `alert_priority: "high"`
3. **Slow Requests**: Requests with `duration_ms > 5000`
4. **Failed Requests**: Requests with `status_code >= 500`

### Integration with Monitoring Tools

The structured JSON format is compatible with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **Datadog**
- **New Relic**
- **CloudWatch Logs Insights**
- **Azure Monitor**

## Troubleshooting

### Common Issues

#### 1. Logs Not Appearing

**Check:**
- Log level configuration (ensure it's not set too high)
- Middleware is properly registered
- Service is using the enhanced logging setup

#### 2. Sensitive Data in Logs

**Solution:**
- Add field pattern to `SENSITIVE_PATTERNS` in enhanced_logging.py or filters
- Review and update redaction rules
- Test with sample data

#### 3. Performance Impact

**Mitigation:**
- Disable request/response body logging in production
- Set appropriate `max_body_size` limits
- Use async logging handlers for high-throughput services

## Migration Guide

### Migrating Existing Services

1. **Update imports**:
   ```python
   from libs.python.common.enhanced_logging import setup_enhanced_logging
   from libs.python.common.logging_middleware import RequestLoggingMiddleware
   ```

2. **Replace setup_logging call**:
   ```python
   # Old
   setup_logging()
   
   # New
   setup_enhanced_logging(
       service_name=settings.app_name,
       environment=settings.environment,
       log_level=settings.log_level,
   )
   ```

3. **Add middleware**:
   ```python
   app.add_middleware(RequestLoggingMiddleware)
   ```

4. **Test thoroughly** in development before deploying to production

## Support

For questions or issues with the enhanced logging system:
1. Check this documentation
2. Review example implementations in existing services
3. Contact the platform team

## Future Enhancements

Planned improvements:
- [ ] Distributed tracing integration (OpenTelemetry)
- [ ] Automatic error grouping and deduplication
- [ ] ML-based anomaly detection
- [ ] Real-time alerting webhooks
- [ ] Log retention and archival policies

