# API Gateway

The API Gateway is the unified entry point for all Draft Genie microservices. It provides authentication, authorization, request routing, and data aggregation across all backend services.

## Features

### 🔐 Authentication & Authorization
- **JWT-based authentication** with Passport.js
- User registration and login endpoints
- Token refresh mechanism
- API key support for service-to-service communication
- Protected routes with JWT guards

### 🔄 Service Proxying
- Automatic routing to backend services:
  - Speaker Service (port 3001)
  - Draft Service (port 3002)
  - RAG Service (port 3003)
  - Evaluation Service (port 3004)
- Request/response transformation
- Error handling and service unavailability detection

### 📊 Data Aggregation
Three powerful aggregation endpoints:

1. **GET /api/v1/speakers/:id/complete** - Complete speaker profile
   - Aggregates speaker data, drafts, evaluations, and metrics
   - Handles partial failures gracefully
   - Returns comprehensive speaker overview

2. **POST /api/v1/workflow/generate-dfn** - DFN Generation Workflow
   - Orchestrates complete DFN generation across multiple services
   - Validates speaker and drafts
   - Triggers RAG service with LangGraph AI
   - Returns workflow status and generated DFN

3. **GET /api/v1/dashboard/metrics** - Dashboard Metrics
   - Aggregates metrics from all services
   - Calculates overall system health
   - Provides service availability status

### 🛡️ Security Features
- Helmet.js for HTTP security headers
- CORS configuration
- Rate limiting (configurable)
- Input validation with class-validator
- Non-root Docker user

### 📚 API Documentation
- Swagger/OpenAPI documentation at `/api/docs`
- Interactive API explorer
- Request/response examples
- Authentication flow documentation

## Architecture

```
API Gateway
├── Authentication Module
│   ├── JWT Strategy
│   ├── API Key Strategy
│   ├── Auth Guards
│   └── User Management (in-memory)
├── Proxy Module
│   ├── HTTP Service
│   ├── Service Discovery
│   └── Error Handling
├── Aggregation Module
│   ├── Speaker Complete
│   └── Dashboard Metrics
├── Workflow Module
│   └── DFN Generation Orchestration
└── Health Module
    ├── Gateway Health
    └── Services Health

```

## Getting Started

### Prerequisites
- Node.js 20+
- npm 10+
- Backend services running (Speaker, Draft, RAG, Evaluation)

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp services/api-gateway/.env.example services/api-gateway/.env

# Edit .env with your configuration
```

### Configuration

Create `.env` file in `services/api-gateway/`:

```env
# Server
PORT=3000
NODE_ENV=development

# JWT Authentication
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRES_IN=24h

# API Keys (comma-separated)
API_KEYS=service-key-1,service-key-2

# CORS
CORS_ORIGIN=http://localhost:3000,http://localhost:4200

# Rate Limiting
THROTTLE_TTL=60000
THROTTLE_LIMIT=100

# Backend Service URLs
SPEAKER_SERVICE_URL=http://localhost:3001
DRAFT_SERVICE_URL=http://localhost:3002
RAG_SERVICE_URL=http://localhost:3003
EVALUATION_SERVICE_URL=http://localhost:3004

# Swagger
SWAGGER_ENABLED=true
SWAGGER_PATH=api/docs
```

### Running the Service

```bash
# Development mode
npm run dev:gateway

# Or with NX
npx nx serve api-gateway

# Production build
npx nx build api-gateway --prod
node dist/services/api-gateway/main.js
```

### Docker

```bash
# Build image
docker build -f docker/Dockerfile.api-gateway -t draft-genie-api-gateway .

# Run container
docker run -p 3000:3000 \
  -e JWT_SECRET=your-secret \
  -e SPEAKER_SERVICE_URL=http://speaker-service:3001 \
  draft-genie-api-gateway

# Or use docker-compose
docker-compose up api-gateway
```

## API Endpoints

### Authentication

#### POST /api/v1/auth/register
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "550e8400-e29b-41d4-a716-446655440000",
  "expiresIn": "24h",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

#### POST /api/v1/auth/login
Login with email and password.

**Request:**
```json
{
  "email": "admin@draftgenie.com",
  "password": "admin123"
}
```

**Response:** Same as register

#### POST /api/v1/auth/refresh
Refresh access token.

**Request:**
```json
{
  "refreshToken": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### GET /api/v1/auth/me
Get current user profile (requires JWT).

**Headers:**
```
Authorization: Bearer <access_token>
```

### Aggregation

#### GET /api/v1/speakers/:id/complete
Get complete speaker data with drafts, evaluations, and metrics.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "speaker": { "id": "123", "name": "John Doe", "bucket": "A" },
  "drafts": {
    "data": [...],
    "error": null
  },
  "evaluations": {
    "data": [...],
    "error": null
  },
  "metrics": {
    "data": {...},
    "error": null
  },
  "summary": {
    "totalDrafts": 5,
    "totalEvaluations": 3,
    "hasMetrics": true
  },
  "aggregatedAt": "2025-10-06T12:00:00Z"
}
```

#### GET /api/v1/dashboard/metrics
Get aggregated dashboard metrics from all services.

**Headers:**
```
Authorization: Bearer <access_token>
```

### Workflow

#### POST /api/v1/workflow/generate-dfn
Orchestrate complete DFN generation workflow.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "speakerId": "123e4567-e89b-12d3-a456-426614174000",
  "prompt": "Generate an improved draft focusing on clarity",
  "context": {
    "topic": "technical documentation",
    "tone": "professional"
  }
}
```

**Response:**
```json
{
  "workflow": {
    "status": "completed",
    "steps": [
      { "step": 1, "name": "validate_speaker", "status": "completed", "data": {...} },
      { "step": 2, "name": "check_drafts", "status": "completed", "data": {...} },
      { "step": 3, "name": "generate_dfn", "status": "completed", "data": {...} },
      { "step": 4, "name": "retrieve_dfn", "status": "completed", "data": {...} }
    ],
    "completedAt": "2025-10-06T12:00:00Z"
  },
  "speaker": { "id": "123", "name": "John Doe", "bucket": "A" },
  "generation": {...},
  "dfn": {...},
  "metadata": {
    "draftCount": 5,
    "prompt": "Generate an improved draft focusing on clarity",
    "usedLangGraph": true
  }
}
```

### Health

#### GET /api/v1/health
Check API Gateway health.

#### GET /api/v1/health/services
Check all backend services health.

## Testing

```bash
# Run unit tests
npx nx test api-gateway

# Run tests with coverage
npx nx test api-gateway --coverage

# Run e2e tests
npx nx test api-gateway --configuration=e2e
```

## Default Credentials

For development/testing, a default admin user is created:

- **Email:** admin@draftgenie.com
- **Password:** admin123

**⚠️ Change these credentials in production!**

## Security Considerations

1. **JWT Secret:** Change `JWT_SECRET` in production to a strong, random value
2. **API Keys:** Use strong, unique API keys for service-to-service communication
3. **CORS:** Configure `CORS_ORIGIN` to only allow trusted domains
4. **Rate Limiting:** Adjust `THROTTLE_LIMIT` based on your needs
5. **HTTPS:** Always use HTTPS in production
6. **User Storage:** Replace in-memory user storage with a proper database

## Troubleshooting

### Service Unavailable Errors
- Check that all backend services are running
- Verify service URLs in `.env` are correct
- Check network connectivity between services

### Authentication Failures
- Verify JWT_SECRET matches across services
- Check token expiration time
- Ensure Authorization header is properly formatted

### Rate Limiting Issues
- Adjust THROTTLE_TTL and THROTTLE_LIMIT in `.env`
- Consider implementing per-user rate limiting

## Contributing

1. Follow NestJS best practices
2. Add tests for new features
3. Update Swagger documentation
4. Follow TypeScript strict mode
5. Use dependency injection

## License

MIT

