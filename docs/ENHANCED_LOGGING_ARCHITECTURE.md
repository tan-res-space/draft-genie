# Enhanced Logging Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Application                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP Request
                             │ X-Request-ID: abc-123
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway (NestJS)                        │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ LoggingInterceptor                                            │ │
│  │  • Generate/Extract Request ID                                │ │
│  │  • Log Request (method, path, headers, body)                  │ │
│  │  • Track Duration                                             │ │
│  │  • Redact Sensitive Data                                      │ │
│  └───────────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ GlobalExceptionFilter                                         │ │
│  │  • Catch Unhandled Exceptions                                 │ │
│  │  • Extract Full Stack Trace                                   │ │
│  │  • Log Error with Context                                     │ │
│  │  • Return Standardized Error Response                         │ │
│  └───────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Proxied Request
                             │ X-Request-ID: abc-123
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Backend Service (FastAPI)                        │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ RequestLoggingMiddleware                                      │ │
│  │  • Extract/Use Request ID                                     │ │
│  │  • Log Request Details                                        │ │
│  │  • Capture Request Body                                       │ │
│  │  • Track Performance Metrics                                  │ │
│  │  • Redact Sensitive Data                                      │ │
│  └───────────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ ErrorTrackingMiddleware                                       │ │
│  │  • Track 5xx Errors                                           │ │
│  │  • Log Server Errors                                          │ │
│  └───────────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Global Exception Handler                                      │ │
│  │  • Catch All Exceptions                                       │ │
│  │  • Format Exception Details                                   │ │
│  │  • Extract Full Stack Trace                                   │ │
│  │  • Log with Request Context                                   │ │
│  └───────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Structured JSON Logs                           │
│  {                                                                  │
│    "timestamp": "2025-10-17T10:30:45.123Z",                        │
│    "level": "ERROR",                                               │
│    "service": "draft-service",                                     │
│    "request_id": "abc-123",                                        │
│    "error": {                                                      │
│      "type": "ValueError",                                         │
│      "traceback": "...",                                           │
│      "stack_frames": [...]                                         │
│    },                                                              │
│    "request": {...},                                               │
│    "requires_investigation": true,                                 │
│    "alert_priority": "high"                                        │
│  }                                                                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Log Aggregation & Analysis                       │
│  • ELK Stack / Splunk / Datadog                                    │
│  • Automated Error Detection                                       │
│  • Alert Generation                                                │
│  • Dashboard Visualization                                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Request Flow with Logging

### 1. Successful Request Flow

```
Client → API Gateway → Backend Service → Database
  │          │              │               │
  │          ▼              ▼               │
  │      Log Request    Log Request         │
  │          │              │               │
  │          │              ▼               │
  │          │         Process Request      │
  │          │              │               │
  │          │              ▼               │
  │          ▼         Log Response         │
  │      Log Response       │               │
  │          │              │               │
  ▼          ▼              ▼               ▼
Response (200 OK)
X-Request-ID: abc-123

Logs Generated:
1. API Gateway: Request received (INFO)
2. Backend: Request received (INFO)
3. Backend: Request completed (INFO)
4. API Gateway: Request completed (INFO)
```

### 2. Error Request Flow

```
Client → API Gateway → Backend Service → Error!
  │          │              │               │
  │          ▼              ▼               │
  │      Log Request    Log Request         │
  │          │              │               │
  │          │              ▼               │
  │          │         Process Request      │
  │          │              │               │
  │          │              ▼               │
  │          │         Exception Raised     │
  │          │              │               │
  │          │              ▼               │
  │          │      Exception Handler       │
  │          │              │               │
  │          │              ▼               │
  │          │      Log Error (ERROR)       │
  │          │      • Full Stack Trace      │
  │          │      • Request Context       │
  │          │      • Error Details         │
  │          │              │               │
  │          ▼              ▼               │
  │      Log Error      Error Response      │
  │          │              │               │
  ▼          ▼              ▼               ▼
Error Response (500)
X-Request-ID: abc-123

Logs Generated:
1. API Gateway: Request received (INFO)
2. Backend: Request received (INFO)
3. Backend: Unhandled exception (ERROR) ← Full stack trace
4. Backend: Request failed (ERROR)
5. API Gateway: Service error (ERROR)
6. API Gateway: Request failed (ERROR)
```

## Component Architecture

### Python Services (FastAPI)

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                    │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Middleware Stack (Order Matters!)                     │ │
│  │                                                       │ │
│  │  1. ErrorTrackingMiddleware                          │ │
│  │     └─ Track 5xx errors specifically                 │ │
│  │                                                       │ │
│  │  2. RequestLoggingMiddleware                         │ │
│  │     ├─ Generate/Extract Request ID                   │ │
│  │     ├─ Log Request Details                           │ │
│  │     ├─ Capture Request Body                          │ │
│  │     ├─ Track Duration                                │ │
│  │     └─ Log Response/Errors                           │ │
│  │                                                       │ │
│  │  3. CORSMiddleware                                   │ │
│  │     └─ Handle CORS                                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Exception Handlers                                    │ │
│  │                                                       │ │
│  │  • HTTPException Handler                             │ │
│  │    └─ Log 4xx errors with context                    │ │
│  │                                                       │ │
│  │  • Global Exception Handler                          │ │
│  │    ├─ Catch all unhandled exceptions                 │ │
│  │    ├─ Format exception details                       │ │
│  │    ├─ Extract full stack trace                       │ │
│  │    └─ Log with request context                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Enhanced Logging                                      │ │
│  │                                                       │ │
│  │  • EnhancedJSONFormatter                             │ │
│  │    ├─ Structured JSON output                         │ │
│  │    ├─ Comprehensive error details                    │ │
│  │    └─ Sensitive data redaction                       │ │
│  │                                                       │ │
│  │  • Context Variables                                 │ │
│  │    ├─ request_id_var                                 │ │
│  │    └─ request_context_var                            │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### TypeScript Services (NestJS)

```
┌─────────────────────────────────────────────────────────────┐
│                      NestJS Application                     │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Global Filters (Applied First)                        │ │
│  │                                                       │ │
│  │  • GlobalExceptionFilter                             │ │
│  │    ├─ Catch all unhandled exceptions                 │ │
│  │    ├─ Extract full stack trace                       │ │
│  │    ├─ Log error with context                         │ │
│  │    ├─ Redact sensitive data                          │ │
│  │    └─ Return standardized error response             │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Global Interceptors                                   │ │
│  │                                                       │ │
│  │  • LoggingInterceptor                                │ │
│  │    ├─ Generate/Extract Request ID                    │ │
│  │    ├─ Log incoming requests                          │ │
│  │    ├─ Track request duration                         │ │
│  │    ├─ Log responses                                  │ │
│  │    ├─ Log errors                                     │ │
│  │    └─ Redact sensitive data                          │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Request Processing                                    │ │
│  │                                                       │ │
│  │  Controllers → Services → Repositories               │ │
│  │       │            │            │                     │ │
│  │       └────────────┴────────────┘                     │ │
│  │              Logging at each layer                    │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Request Context Extraction

```
HTTP Request
    │
    ├─ Method (GET, POST, etc.)
    ├─ Path (/api/v1/drafts)
    ├─ URL (full URL with query params)
    ├─ Headers
    │   ├─ Authorization → [REDACTED]
    │   ├─ Content-Type
    │   └─ X-Request-ID
    ├─ Body
    │   ├─ password → [REDACTED]
    │   ├─ api_key → [REDACTED]
    │   └─ other fields
    ├─ Query Parameters
    ├─ Client Info
    │   ├─ IP Address
    │   └─ Port
    └─ User Info (if authenticated)
        └─ User ID

    ↓ Redaction Applied ↓

Logged Request Context (Safe)
```

### Error Details Extraction

```
Exception Raised
    │
    ├─ Exception Type (ValueError, etc.)
    ├─ Exception Message
    ├─ Exception Args
    ├─ Full Traceback
    │   └─ Complete stack trace string
    ├─ Stack Frames (Structured)
    │   ├─ Frame 1
    │   │   ├─ File path
    │   │   ├─ Function name
    │   │   ├─ Line number
    │   │   └─ Code context
    │   ├─ Frame 2
    │   │   └─ ...
    │   └─ Frame N
    ├─ Local Variables (Optional, Redacted)
    └─ Custom Attributes

    ↓ Formatting Applied ↓

Structured Error Log
```

## Sensitive Data Redaction Flow

```
Input Data
    │
    ├─ username: "john.doe"
    ├─ password: "secret123"
    ├─ email: "john@example.com"
    ├─ api_key: "sk_live_abc123"
    └─ token: "eyJhbGci..."

    ↓ Pattern Matching ↓

Redaction Rules Applied
    │
    ├─ Check field name against patterns
    │   ├─ password → MATCH → Redact
    │   ├─ api_key → MATCH → Redact
    │   ├─ token → MATCH → Redact
    │   └─ username → NO MATCH → Keep
    │
    └─ Check value patterns
        └─ Long alphanumeric strings → Redact

    ↓ Redaction Applied ↓

Output Data (Safe)
    │
    ├─ username: "john.doe"
    ├─ password: "[REDACTED]"
    ├─ email: "john@example.com"
    ├─ api_key: "[REDACTED]"
    └─ token: "[REDACTED]"
```

## Log Aggregation Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Services                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Gateway  │  │ Speaker  │  │  Draft   │  │   RAG    │   │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │             │          │
│       └─────────────┴──────────────┴─────────────┘          │
│                     │                                       │
│              Structured JSON Logs                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Log Collection Layer                       │
│  • Filebeat / Fluentd / CloudWatch Agent                   │
│  • Parse JSON logs                                          │
│  • Add metadata (host, environment, etc.)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Log Storage & Indexing                     │
│  • Elasticsearch / Splunk / CloudWatch Logs                │
│  • Index by timestamp, service, level, request_id          │
│  • Full-text search on error messages                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Analysis & Visualization                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Dashboards │  │   Alerts    │  │   Queries   │        │
│  │  • Errors   │  │  • High     │  │  • Request  │        │
│  │  • Metrics  │  │    Priority │  │    Tracing  │        │
│  │  • Trends   │  │  • Anomaly  │  │  • Error    │        │
│  │             │  │             │  │    Analysis │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                          │
│                                                             │
│  Layer 1: Input Validation                                 │
│  ├─ Validate request data                                  │
│  └─ Sanitize inputs                                        │
│                                                             │
│  Layer 2: Sensitive Data Detection                         │
│  ├─ Pattern matching on field names                        │
│  ├─ Pattern matching on values                             │
│  └─ Context-aware detection                                │
│                                                             │
│  Layer 3: Redaction                                        │
│  ├─ Replace sensitive values with [REDACTED]              │
│  ├─ Preserve data structure                                │
│  └─ Maintain log readability                               │
│                                                             │
│  Layer 4: Log Output                                       │
│  ├─ Write to secure log destination                        │
│  ├─ Apply access controls                                  │
│  └─ Encrypt in transit/at rest                             │
│                                                             │
│  Layer 5: Audit & Compliance                               │
│  ├─ Log access tracking                                    │
│  ├─ Retention policies                                     │
│  └─ Compliance reporting                                   │
└─────────────────────────────────────────────────────────────┘
```

## Performance Considerations

```
Request Processing Time
│
├─ Without Enhanced Logging: ~10ms
│
└─ With Enhanced Logging: ~12ms (+2ms overhead)
    │
    ├─ Request ID Generation: <1ms
    ├─ Context Extraction: <1ms
    ├─ Sensitive Data Redaction: <1ms
    ├─ JSON Formatting: <1ms
    └─ Log Writing: <1ms

Optimization Strategies:
├─ Async log writing
├─ Body size limits (10KB default)
├─ Conditional body logging
├─ Efficient JSON serialization
└─ Minimal regex operations
```

---

**Document Version**: 1.0  
**Last Updated**: October 17, 2025

