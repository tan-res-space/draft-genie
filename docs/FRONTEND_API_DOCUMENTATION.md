# DraftGenie API Documentation for Frontend Development

## 🌐 Base URL

**Production (Azure):**
```
https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io
```

**API Base Path:**
```
/api/v1
```

**Full Base URL:**
```
https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1
```

---

## 📚 Interactive API Documentation

### Swagger UI (Recommended)
```
https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/docs
```

**Features:**
- Interactive API explorer
- Try out endpoints directly
- View request/response schemas
- See example payloads
- Test authentication

---

## 🔐 Authentication

### Overview
DraftGenie uses **JWT (JSON Web Token)** based authentication. All protected endpoints require a valid JWT token in the Authorization header.

### Authentication Flow

#### 1. Register a New User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  },
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": "24h"
}
```

#### 2. Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  },
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": "24h"
}
```

#### 3. Using the Access Token

Include the access token in the Authorization header for all protected endpoints:

```http
GET /api/v1/speakers
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 4. Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": "24h"
}
```

#### 5. Get Current User Profile
```http
GET /api/v1/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user"
}
```

#### 6. Logout
```http
POST /api/v1/auth/logout
Content-Type: application/json

{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (204 No Content)**

---

## 👥 Speaker Management

### 1. Create Speaker (SSA - Speaker Self-Addition)
```http
POST /api/v1/speakers
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Dr. John Smith",
  "email": "john.smith@hospital.com",
  "bucket": "GOOD",
  "externalId": "instanote-speaker-12345",
  "notes": "Cardiologist with 15 years of experience",
  "metadata": {
    "specialty": "Cardiology",
    "hospital": "General Hospital"
  }
}
```

**Bucket Types:** `EXCELLENT`, `GOOD`, `AVERAGE`, `POOR`, `NEEDS_IMPROVEMENT`

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "externalId": "instanote-speaker-12345",
  "name": "Dr. John Smith",
  "email": "john.smith@hospital.com",
  "bucket": "GOOD",
  "status": "ACTIVE",
  "notes": "Cardiologist with 15 years of experience",
  "metadata": {
    "specialty": "Cardiology",
    "hospital": "General Hospital"
  },
  "createdAt": "2025-10-16T10:30:00Z",
  "updatedAt": "2025-10-16T10:30:00Z"
}
```

### 2. Get All Speakers (Paginated)
```http
GET /api/v1/speakers?page=1&limit=20&bucket=GOOD&status=ACTIVE&search=John&sortBy=createdAt&sortOrder=desc
Authorization: Bearer {token}
```

**Query Parameters:**
- `page` (number, default: 1) - Page number
- `limit` (number, default: 20) - Items per page
- `bucket` (string, optional) - Filter by bucket
- `status` (string, optional) - Filter by status (ACTIVE, INACTIVE, PENDING, ARCHIVED)
- `search` (string, optional) - Search by name or email
- `sortBy` (string, default: createdAt) - Sort field
- `sortOrder` (string, default: desc) - Sort order (asc, desc)

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Dr. John Smith",
      "email": "john.smith@hospital.com",
      "bucket": "GOOD",
      "status": "ACTIVE",
      "metadata": {},
      "createdAt": "2025-10-16T10:30:00Z",
      "updatedAt": "2025-10-16T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "totalPages": 8,
    "hasNext": true,
    "hasPrevious": false
  }
}
```

### 3. Get Speaker by ID
```http
GET /api/v1/speakers/{speakerId}
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "externalId": "instanote-speaker-12345",
  "name": "Dr. John Smith",
  "email": "john.smith@hospital.com",
  "bucket": "GOOD",
  "status": "ACTIVE",
  "notes": "Cardiologist with 15 years of experience",
  "metadata": {
    "specialty": "Cardiology",
    "totalDrafts": 45,
    "averageQualityScore": 0.92
  },
  "createdAt": "2025-10-16T10:30:00Z",
  "updatedAt": "2025-10-16T10:30:00Z"
}
```

### 4. Update Speaker
```http
PATCH /api/v1/speakers/{speakerId}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Dr. John Smith Jr.",
  "email": "john.smith.jr@hospital.com",
  "status": "ACTIVE",
  "notes": "Updated notes",
  "metadata": {
    "specialty": "Cardiology",
    "yearsOfExperience": 16
  }
}
```

**Response (200 OK):** Same as Get Speaker by ID

### 5. Update Speaker Bucket
```http
PUT /api/v1/speakers/{speakerId}/bucket
Authorization: Bearer {token}
Content-Type: application/json

{
  "bucket": "EXCELLENT",
  "reason": "Improved quality metrics"
}
```

**Response (200 OK):** Same as Get Speaker by ID

### 6. Delete Speaker (Soft Delete)
```http
DELETE /api/v1/speakers/{speakerId}
Authorization: Bearer {token}
```

**Response (204 No Content)**

### 7. Get Speaker Statistics
```http
GET /api/v1/speakers/statistics
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "total": 500,
  "byBucket": {
    "EXCELLENT": 50,
    "GOOD": 200,
    "AVERAGE": 150,
    "POOR": 75,
    "NEEDS_IMPROVEMENT": 25
  },
  "byStatus": {
    "ACTIVE": 450,
    "INACTIVE": 30,
    "PENDING": 15,
    "ARCHIVED": 5
  }
}
```

---

## 📝 Draft Management

### 1. Ingest Drafts for Speaker
```http
POST /api/v1/drafts/ingest?speaker_id={speakerId}&limit=10
Authorization: Bearer {token}
```

**Query Parameters:**
- `speaker_id` (string, required) - Speaker UUID
- `limit` (number, default: 10, max: 100) - Number of drafts to ingest

**Response (201 Created):**
```json
{
  "message": "Successfully ingested 10 drafts",
  "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
  "count": 10,
  "draft_ids": ["draft_001", "draft_002", "..."]
}
```

### 2. Create Draft Manually
```http
POST /api/v1/drafts
Authorization: Bearer {token}
Content-Type: application/json

{
  "draft_id": "draft_123456",
  "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
  "draft_type": "AD",
  "original_text": "The patient has a history of diabetis.",
  "corrected_text": "The patient has a history of diabetes.",
  "word_count": 8,
  "correction_count": 1,
  "metadata": {
    "source": "instanote"
  },
  "dictated_at": "2025-10-16T10:00:00Z"
}
```

**Draft Types:** `AD` (Actual Draft), `LD` (Learning Draft), `IFN` (Initial From Notes)

**Response (201 Created):**
```json
{
  "_id": "67123abc456def789012",
  "draft_id": "draft_123456",
  "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
  "draft_type": "AD",
  "original_text": "The patient has a history of diabetis.",
  "corrected_text": "The patient has a history of diabetes.",
  "word_count": 8,
  "correction_count": 1,
  "metadata": {
    "source": "instanote"
  },
  "dictated_at": "2025-10-16T10:00:00Z",
  "created_at": "2025-10-16T10:30:00Z",
  "updated_at": "2025-10-16T10:30:00Z",
  "is_processed": false,
  "vector_generated": false
}
```

### 3. Get All Drafts
```http
GET /api/v1/drafts?skip=0&limit=100&draft_type=AD&is_processed=false
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip` (number, default: 0) - Number of records to skip
- `limit` (number, default: 100, max: 1000) - Maximum records
- `draft_type` (string, optional) - Filter by type (AD, LD, IFN)
- `is_processed` (boolean, optional) - Filter by processing status

**Response (200 OK):** Array of draft objects

### 4. Get Draft by ID
```http
GET /api/v1/drafts/{draftId}
Authorization: Bearer {token}
```

**Response (200 OK):** Single draft object

### 5. Get Drafts by Speaker
```http
GET /api/v1/drafts/speaker/{speakerId}?skip=0&limit=100
Authorization: Bearer {token}
```

**Response (200 OK):** Array of draft objects for the speaker

---

## 🔄 Cross-Service Aggregation

### 1. Get Complete Speaker Data
```http
GET /api/v1/speakers/{speakerId}/complete
Authorization: Bearer {token}
```

**Description:** Aggregates data from Speaker, Draft, and Evaluation services

**Response (200 OK):**
```json
{
  "speaker": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Dr. John Smith",
    "bucket": "GOOD",
    "status": "ACTIVE"
  },
  "drafts": {
    "data": [...],
    "error": null
  },
  "evaluations": {
    "data": [...],
    "error": null
  },
  "metrics": {
    "data": {
      "totalDrafts": 45,
      "averageQualityScore": 0.92
    },
    "error": null
  },
  "summary": {
    "totalDrafts": 45,
    "totalEvaluations": 12,
    "hasMetrics": true
  },
  "aggregatedAt": "2025-10-16T10:30:00Z"
}
```

### 2. Get Dashboard Metrics
```http
GET /api/v1/dashboard/metrics
Authorization: Bearer {token}
```

**Description:** Aggregates metrics from all services for dashboard

**Response (200 OK):**
```json
{
  "speakers": {
    "data": {
      "total": 500,
      "byBucket": {...}
    },
    "error": null
  },
  "drafts": {
    "data": {
      "total": 5000,
      "byType": {...}
    },
    "error": null
  },
  "evaluations": {
    "data": {
      "total": 1200,
      "completed": 1000
    },
    "error": null
  },
  "summary": {
    "totalSpeakers": 500,
    "totalDrafts": 5000,
    "totalEvaluations": 1200,
    "servicesHealthy": 4,
    "servicesTotal": 4,
    "healthPercentage": 100
  },
  "aggregatedAt": "2025-10-16T10:30:00Z"
}
```

---

## 🤖 AI Workflow - DFN Generation

### Generate DFN (Draft From Notes)
```http
POST /api/v1/workflow/generate-dfn
Authorization: Bearer {token}
Content-Type: application/json

{
  "speakerId": "550e8400-e29b-41d4-a716-446655440000",
  "prompt": "Generate a professional medical note",
  "options": {
    "useLangGraph": true,
    "maxTokens": 2000
  }
}
```

**Description:** Orchestrates complete DFN generation workflow:
1. Validates speaker exists
2. Checks for existing drafts (IFN)
3. Triggers RAG service with LangGraph AI
4. Returns generated DFN

**Response (201 Created):**
```json
{
  "workflow": {
    "status": "completed",
    "steps": [
      {
        "step": 1,
        "name": "Validate Speaker",
        "status": "success",
        "data": {...}
      },
      {
        "step": 2,
        "name": "Check Drafts",
        "status": "success",
        "data": {...}
      },
      {
        "step": 3,
        "name": "Generate DFN",
        "status": "success",
        "data": {...}
      }
    ],
    "completedAt": "2025-10-16T10:35:00Z"
  },
  "speaker": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Dr. John Smith",
    "bucket": "GOOD"
  },
  "generation": {
    "dfn_text": "Generated medical note...",
    "confidence": 0.95
  },
  "dfn": {
    "draft_id": "dfn_789012",
    "created_at": "2025-10-16T10:35:00Z"
  },
  "metadata": {
    "draftCount": 45,
    "prompt": "Generate a professional medical note",
    "usedLangGraph": true
  }
}
```

---

## ❤️ Health Check

### 1. API Gateway Health
```http
GET /api/v1/health
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "timestamp": "2025-10-16T10:30:00Z",
  "uptime": 86400,
  "version": "1.0.0"
}
```

### 2. All Services Health
```http
GET /api/v1/health/services
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "gateway": {
    "status": "healthy",
    "responseTime": 5
  },
  "speaker": {
    "status": "healthy",
    "responseTime": 12
  },
  "draft": {
    "status": "healthy",
    "responseTime": 15
  },
  "rag": {
    "status": "healthy",
    "responseTime": 20
  },
  "evaluation": {
    "status": "healthy",
    "responseTime": 18
  },
  "summary": {
    "total": 5,
    "healthy": 5,
    "unhealthy": 0,
    "healthPercentage": 100
  }
}
```

---

## ⚠️ Error Handling

### Standard Error Response Format

All errors follow a consistent format:

```json
{
  "statusCode": 400,
  "message": "Validation failed",
  "error": "Bad Request",
  "timestamp": "2025-10-16T10:30:00Z",
  "path": "/api/v1/speakers"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request successful, no content to return |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Common Error Examples

#### 401 Unauthorized
```json
{
  "statusCode": 401,
  "message": "Unauthorized",
  "error": "Unauthorized"
}
```

#### 404 Not Found
```json
{
  "statusCode": 404,
  "message": "Speaker not found",
  "error": "Not Found"
}
```

#### 400 Validation Error
```json
{
  "statusCode": 400,
  "message": [
    "name must be longer than or equal to 2 characters",
    "email must be an email"
  ],
  "error": "Bad Request"
}
```

#### 409 Conflict
```json
{
  "statusCode": 409,
  "message": "Speaker with external ID already exists",
  "error": "Conflict"
}
```

---

## 🚦 Rate Limiting

### Limits
- **Default**: 100 requests per minute per IP address
- **Authenticated**: 200 requests per minute per user

### Rate Limit Headers

Every response includes rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1697456400
```

### Rate Limit Exceeded Response

```json
{
  "statusCode": 429,
  "message": "Too Many Requests",
  "error": "ThrottlerException: Too Many Requests"
}
```

---

## 🔒 CORS Configuration

### Allowed Origins
- Development: `http://localhost:3000`, `http://localhost:4200`
- Production: Configured based on deployment

### Allowed Methods
- GET, POST, PUT, PATCH, DELETE, OPTIONS

### Allowed Headers
- Content-Type, Authorization, X-Requested-With

---

## 📦 Data Models

### Speaker Model

```typescript
interface Speaker {
  id: string;                    // UUID
  externalId?: string;           // External system ID
  name: string;                  // Speaker name
  email?: string;                // Email address
  bucket: BucketType;            // Quality bucket
  status: SpeakerStatus;         // Current status
  notes?: string;                // Additional notes
  metadata: Record<string, any>; // Custom metadata
  createdAt: Date;               // Creation timestamp
  updatedAt: Date;               // Last update timestamp
  deletedAt?: Date;              // Soft delete timestamp
}

enum BucketType {
  EXCELLENT = 'EXCELLENT',
  GOOD = 'GOOD',
  AVERAGE = 'AVERAGE',
  POOR = 'POOR',
  NEEDS_IMPROVEMENT = 'NEEDS_IMPROVEMENT'
}

enum SpeakerStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  PENDING = 'PENDING',
  ARCHIVED = 'ARCHIVED'
}
```

### Draft Model

```typescript
interface Draft {
  _id: string;                   // MongoDB ObjectId
  draft_id: string;              // Unique draft ID
  speaker_id: string;            // Speaker UUID
  draft_type: DraftType;         // Type of draft
  original_text: string;         // Original dictated text
  corrected_text: string;        // Corrected text
  word_count: number;            // Word count
  correction_count: number;      // Number of corrections
  metadata: Record<string, any>; // Additional metadata
  dictated_at?: Date;            // Dictation timestamp
  created_at: Date;              // Creation timestamp
  updated_at: Date;              // Last update timestamp
  is_processed: boolean;         // Processing status
  vector_generated: boolean;     // Vector generation status
}

enum DraftType {
  AD = 'AD',   // Actual Draft
  LD = 'LD',   // Learning Draft
  IFN = 'IFN'  // Initial From Notes
}
```

---



## 🛠️ Frontend Integration Examples

### React/TypeScript Example

```typescript
// API Client Setup
import axios from 'axios';

const API_BASE_URL = 'https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refreshToken,
          });
          localStorage.setItem('accessToken', data.accessToken);
          localStorage.setItem('refreshToken', data.refreshToken);

          // Retry original request
          error.config.headers.Authorization = `Bearer ${data.accessToken}`;
          return axios(error.config);
        } catch (refreshError) {
          // Redirect to login
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Example: Login
async function login(email: string, password: string) {
  const { data } = await apiClient.post('/auth/login', { email, password });
  localStorage.setItem('accessToken', data.accessToken);
  localStorage.setItem('refreshToken', data.refreshToken);
  return data.user;
}

// Example: Get Speakers
async function getSpeakers(page = 1, limit = 20) {
  const { data } = await apiClient.get('/speakers', {
    params: { page, limit },
  });
  return data;
}

// Example: Create Speaker
async function createSpeaker(speakerData: CreateSpeakerDto) {
  const { data } = await apiClient.post('/speakers', speakerData);
  return data;
}

// Example: Generate DFN
async function generateDFN(speakerId: string, prompt: string) {
  const { data } = await apiClient.post('/workflow/generate-dfn', {
    speakerId,
    prompt,
    options: { useLangGraph: true },
  });
  return data;
}
```

### Vue.js Example

```javascript
// composables/useApi.js
import { ref } from 'vue';

const API_BASE_URL = 'https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1';

export function useApi() {
  const loading = ref(false);
  const error = ref(null);

  async function request(endpoint, options = {}) {
    loading.value = true;
    error.value = null;

    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
          ...options.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  }

  return { request, loading, error };
}
```

### Angular Example

```typescript
// services/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1';

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('accessToken');
    return new HttpHeaders({
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` })
    });
  }

  getSpeakers(page: number = 1, limit: number = 20): Observable<any> {
    return this.http.get(`${this.baseUrl}/speakers`, {
      headers: this.getHeaders(),
      params: { page: page.toString(), limit: limit.toString() }
    });
  }

  createSpeaker(speakerData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/speakers`, speakerData, {
      headers: this.getHeaders()
    });
  }
}
```

---

## 📞 Support & Resources

### Documentation
- **Swagger UI**: https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/docs
- **Health Check**: https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health

### Service Status
Check the health of all services:
```bash
curl https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health/services
```

### Testing
Use the Swagger UI for interactive testing and exploring all available endpoints.

---

## 🔄 Changelog

### Version 1.0.0 (2025-10-16)
- Initial API release
- Authentication with JWT
- Speaker management endpoints
- Draft management endpoints
- Cross-service aggregation
- DFN generation workflow
- Health check endpoints

---

**Last Updated**: 2025-10-16
**API Version**: 1.0.0
**Status**: ✅ Production Ready
