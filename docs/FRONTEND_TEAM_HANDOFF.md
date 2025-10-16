# DraftGenie Backend API - Frontend Team Handoff

## 📋 Overview

The DraftGenie backend services are now **deployed and running on Azure**. This document provides all the information your frontend team needs to integrate with the APIs.

---

## 🌐 Production Environment

### API Gateway (Main Entry Point)
```
https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io
```

### API Base Path
```
/api/v1
```

### Full Base URL
```
https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1
```

---

## 📚 Documentation Resources

### 1. Interactive API Documentation (Swagger UI) ⭐ **START HERE**
```
https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/docs
```

**Features:**
- ✅ Interactive API explorer
- ✅ Try endpoints directly in browser
- ✅ View all request/response schemas
- ✅ See example payloads
- ✅ Test authentication flow

### 2. Complete API Documentation
📄 **File**: `docs/FRONTEND_API_DOCUMENTATION.md`

**Contents:**
- Complete endpoint reference
- Authentication flow
- Request/response examples
- Error handling
- Data models
- Frontend integration examples (React, Vue, Angular)

### 3. Quick Reference Guide
📄 **File**: `docs/API_QUICK_REFERENCE.md`

**Contents:**
- Quick endpoint lookup table
- Common examples
- Enums and constants
- HTTP status codes

### 4. Postman Collection
📄 **File**: `docs/DraftGenie_API.postman_collection.json`

**How to use:**
1. Open Postman
2. Import the collection file
3. Set the `baseUrl` variable (already configured)
4. Start testing!

---

## 🔑 Key Information

### Authentication
- **Type**: JWT (JSON Web Token)
- **Token Lifetime**: 24 hours
- **Refresh Token**: Available for token renewal

### Authorization Header Format
```
Authorization: Bearer {your-access-token}
```

### CORS
- ✅ Enabled for frontend origins
- ✅ Supports all standard HTTP methods
- ✅ Credentials allowed

### Rate Limiting
- **Unauthenticated**: 100 requests/minute
- **Authenticated**: 200 requests/minute

---

## 🚀 Quick Start Guide

### Step 1: Test the API
Visit the Swagger UI and try the health check endpoint:
```
GET /api/v1/health
```

### Step 2: Register a Test User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "TestPassword123!",
  "name": "Test User"
}
```

### Step 3: Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "TestPassword123!"
}
```

**Response includes:**
- `accessToken` - Use this for API calls
- `refreshToken` - Use this to get new access tokens
- `user` - User profile information

### Step 4: Make Authenticated Requests
```http
GET /api/v1/speakers
Authorization: Bearer {accessToken}
```

---

## 📊 Available Services

### 1. **Authentication Service**
- User registration
- Login/logout
- Token refresh
- User profile management

### 2. **Speaker Service**
- Create and manage speakers
- Query speakers with filters
- Update speaker buckets
- Get speaker statistics

### 3. **Draft Service**
- Ingest drafts from InstaNote
- Create drafts manually
- Query drafts by speaker
- Filter drafts by type and status

### 4. **Aggregation Service**
- Get complete speaker data (speaker + drafts + evaluations)
- Get dashboard metrics
- Cross-service data aggregation

### 5. **AI Workflow Service**
- Generate DFN (Draft From Notes) using AI
- LangGraph-powered workflows
- Multi-step orchestration

---

## 🎯 Common Use Cases

### Use Case 1: Display Speaker List
```javascript
// GET /api/v1/speakers?page=1&limit=20&status=ACTIVE
const response = await fetch(
  'https://api-gateway.../api/v1/speakers?page=1&limit=20&status=ACTIVE',
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
);
const { data, pagination } = await response.json();
```

### Use Case 2: Create New Speaker
```javascript
// POST /api/v1/speakers
const response = await fetch(
  'https://api-gateway.../api/v1/speakers',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'Dr. John Smith',
      email: 'john@hospital.com',
      bucket: 'GOOD'
    })
  }
);
const speaker = await response.json();
```

### Use Case 3: Get Complete Speaker Profile
```javascript
// GET /api/v1/speakers/{id}/complete
const response = await fetch(
  `https://api-gateway.../api/v1/speakers/${speakerId}/complete`,
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
);
const { speaker, drafts, evaluations, metrics } = await response.json();
```

### Use Case 4: Generate AI-Powered DFN
```javascript
// POST /api/v1/workflow/generate-dfn
const response = await fetch(
  'https://api-gateway.../api/v1/workflow/generate-dfn',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      speakerId: '550e8400-e29b-41d4-a716-446655440000',
      prompt: 'Generate a professional medical note',
      options: { useLangGraph: true }
    })
  }
);
const { workflow, generation, dfn } = await response.json();
```

---

## 🔧 Integration Code Examples

### React/TypeScript
See `docs/FRONTEND_API_DOCUMENTATION.md` section "Frontend Integration Examples"

**Includes:**
- Axios setup with interceptors
- Token refresh handling
- Error handling
- Example API calls

### Vue.js
See `docs/FRONTEND_API_DOCUMENTATION.md` section "Frontend Integration Examples"

**Includes:**
- Composable for API calls
- Loading and error states
- Fetch API usage

### Angular
See `docs/FRONTEND_API_DOCUMENTATION.md` section "Frontend Integration Examples"

**Includes:**
- Service setup
- HttpClient usage
- Observable patterns

---

## 📦 Data Models

### Speaker
```typescript
{
  id: string;                    // UUID
  name: string;
  email?: string;
  bucket: 'EXCELLENT' | 'GOOD' | 'AVERAGE' | 'POOR' | 'NEEDS_IMPROVEMENT';
  status: 'ACTIVE' | 'INACTIVE' | 'PENDING' | 'ARCHIVED';
  metadata: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}
```

### Draft
```typescript
{
  _id: string;                   // MongoDB ID
  draft_id: string;
  speaker_id: string;
  draft_type: 'AD' | 'LD' | 'IFN';
  original_text: string;
  corrected_text: string;
  word_count: number;
  correction_count: number;
  created_at: Date;
  is_processed: boolean;
}
```

---

## ⚠️ Important Notes

### 1. Token Management
- Store `accessToken` and `refreshToken` securely (localStorage or secure cookie)
- Implement automatic token refresh on 401 responses
- Clear tokens on logout

### 2. Error Handling
- All errors follow consistent format with `statusCode`, `message`, `error`
- Handle 401 (Unauthorized) by refreshing token or redirecting to login
- Handle 429 (Rate Limit) by implementing retry logic

### 3. Pagination
- Most list endpoints support pagination
- Use `page` and `limit` query parameters
- Response includes `pagination` object with metadata

### 4. CORS
- API is configured to accept requests from your frontend domain
- If you encounter CORS issues, contact backend team

---

## 🆘 Support & Troubleshooting

### Health Check
Always available (no auth required):
```
GET https://api-gateway.../api/v1/health
```

### Service Status
Check all services (auth required):
```
GET https://api-gateway.../api/v1/health/services
```

### Common Issues

**Issue**: 401 Unauthorized
- **Solution**: Check if token is valid and not expired. Try refreshing the token.

**Issue**: 429 Too Many Requests
- **Solution**: Implement rate limiting on frontend. Wait before retrying.

**Issue**: CORS Error
- **Solution**: Verify your frontend domain is whitelisted. Contact backend team.

**Issue**: 404 Not Found
- **Solution**: Verify the endpoint URL and HTTP method are correct.

---

## 📞 Contact

For questions or issues:
1. Check the Swagger documentation first
2. Review the complete API documentation
3. Test with Postman collection
4. Contact backend team if issues persist

---

## ✅ Checklist for Frontend Team

- [ ] Review Swagger UI documentation
- [ ] Import Postman collection and test endpoints
- [ ] Read complete API documentation
- [ ] Set up authentication flow in your app
- [ ] Implement token refresh logic
- [ ] Test speaker CRUD operations
- [ ] Test draft retrieval
- [ ] Test aggregation endpoints
- [ ] Implement error handling
- [ ] Test rate limiting behavior
- [ ] Set up environment variables for API URL

---

**API Version**: 1.0.0  
**Last Updated**: 2025-10-16  
**Status**: ✅ Production Ready  
**Deployment**: Azure Container Apps (South India)

