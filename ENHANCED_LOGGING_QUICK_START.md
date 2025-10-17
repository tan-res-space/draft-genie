# Enhanced Logging - Quick Start Guide

## What's New?

DraftGenie now has comprehensive error logging that captures:
- ✅ Full stack traces for all exceptions
- ✅ Complete request context (method, path, headers, body)
- ✅ Automatic sensitive data redaction (passwords, tokens, PII)
- ✅ Structured JSON logs for automated analysis
- ✅ Request correlation via unique request IDs
- ✅ Performance metrics (request duration, response size)

## Quick Test

### 1. Run the Test Suite

```bash
# Test the enhanced logging functionality
python tests/test_enhanced_logging.py
```

Expected output:
```
=== Testing Sensitive Data Redaction ===
✅ Sensitive data redaction test passed!

=== Testing Exception Formatting ===
✅ Exception formatting test passed!

=== Testing JSON Formatter ===
✅ JSON formatter test passed!

=== Testing Error Logging ===
✅ Error logging test passed!

✅ All tests passed!
```

### 2. Test with a Real Service

```bash
# Start the draft service
cd services/draft-service
poetry run uvicorn app.main:app --reload

# In another terminal, make a test request
curl -X POST http://localhost:3002/api/v1/drafts \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-123" \
  -d '{
    "speaker_id": "test-speaker",
    "content": "Test draft content",
    "password": "secret123"
  }'
```

Check the logs - you should see:
- Structured JSON output
- Request ID: `test-123`
- Password field redacted: `"password": "[REDACTED]"`
- Full request context

### 3. Trigger an Error

```bash
# Trigger a 404 error
curl http://localhost:3002/api/v1/drafts/nonexistent-id

# Check logs for:
# - Full stack trace
# - Error classification
# - Alert priority
```

## Log Format Example

```json
{
  "timestamp": "2025-10-17T10:30:45.123Z",
  "level": "ERROR",
  "severity": "ERROR",
  "service": "draft-service",
  "environment": "development",
  "request_id": "test-123",
  "message": "Unhandled exception: ValueError: Invalid draft ID",
  "request": {
    "method": "POST",
    "path": "/api/v1/drafts",
    "headers": {
      "content-type": "application/json",
      "authorization": "[REDACTED]"
    },
    "body": {
      "speaker_id": "test-speaker",
      "password": "[REDACTED]"
    }
  },
  "error": {
    "type": "ValueError",
    "message": "Invalid draft ID",
    "traceback": "Traceback (most recent call last):\n  File ...",
    "stack_frames": [
      {
        "file": "/app/services/draft_service.py",
        "function": "create_draft",
        "line_number": 145,
        "code_context": "draft = Draft(id=draft_id)"
      }
    ]
  },
  "requires_investigation": true,
  "alert_priority": "high"
}
```

## What Gets Redacted?

Automatically redacted fields:
- `password`, `passwd`, `pwd`
- `secret`, `token`, `api_key`
- `authorization`, `bearer`, `jwt`
- `session`, `cookie`, `csrf`
- `ssn`, `credit_card`, `cvv`, `pin`
- `private_key`, `access_token`, `refresh_token`

## Services Updated

### Python Services (FastAPI)
- ✅ Draft Service
- ✅ RAG Service
- ✅ Evaluation Service

### TypeScript Services (NestJS)
- ✅ API Gateway
- ✅ Speaker Service

## Configuration

### Environment Variables

```bash
# Python services
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json             # json or text
ENVIRONMENT=production      # development, staging, production

# TypeScript services
LOG_LEVEL=info              # debug, info, warn, error
NODE_ENV=production         # development, production
```

## Querying Logs

### Find All Errors

```bash
# Using jq to filter JSON logs
cat logs/application.log | jq 'select(.level == "ERROR")'
```

### Find by Request ID

```bash
cat logs/application.log | jq 'select(.request_id == "test-123")'
```

### Find High Priority Alerts

```bash
cat logs/application.log | jq 'select(.alert_priority == "high")'
```

### Group Errors by Type

```bash
cat logs/application.log | jq -r '.error.type' | sort | uniq -c | sort -rn
```

## Best Practices

### ✅ DO

```python
# Include context in error logs
logger.error(
    f"Failed to create draft for speaker {speaker_id}",
    exc_info=True,
    extra={
        "extra_data": {
            "speaker_id": speaker_id,
            "draft_type": draft_type,
        }
    }
)

# Use appropriate log levels
logger.debug("Detailed debugging info")
logger.info("Normal operation")
logger.warning("Unexpected but handled")
logger.error("Needs investigation", exc_info=True)
logger.critical("Critical failure", exc_info=True)
```

### ❌ DON'T

```python
# Don't log sensitive data manually
logger.info(f"User password: {password}")  # ❌ BAD

# Don't skip exc_info for exceptions
logger.error(f"Error: {e}")  # ❌ Missing stack trace

# Don't use wrong log levels
logger.error("User logged in")  # ❌ Not an error
```

## Monitoring Integration

The structured JSON format works with:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- Datadog
- New Relic
- CloudWatch Logs Insights
- Azure Monitor

## Troubleshooting

### Logs Not Appearing?

1. Check log level: `LOG_LEVEL=DEBUG`
2. Verify middleware is registered
3. Check service is using enhanced logging setup

### Sensitive Data in Logs?

1. Add pattern to `SENSITIVE_PATTERNS`
2. Test with sample data
3. Review redaction rules

### Performance Issues?

1. Disable request body logging: `log_request_body=False`
2. Reduce max body size: `max_body_size=5000`
3. Increase log level: `LOG_LEVEL=WARNING`

## Full Documentation

📚 **Comprehensive Guide**: `docs/ENHANCED_LOGGING_GUIDE.md`

Includes:
- Detailed architecture
- Configuration examples
- Best practices
- Migration guide
- Monitoring setup

## Support

Questions? Check:
1. This quick start guide
2. Full documentation: `docs/ENHANCED_LOGGING_GUIDE.md`
3. Implementation summary: `ENHANCED_LOGGING_IMPLEMENTATION_SUMMARY.md`
4. Example implementations in updated services

---

**Status**: ✅ Ready to Use
**Version**: 1.0
**Last Updated**: October 17, 2025

