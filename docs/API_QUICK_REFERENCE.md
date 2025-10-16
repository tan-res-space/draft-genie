# DraftGenie API - Quick Reference

## 🌐 Base URL
```
https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1
```

## 📚 Swagger Documentation
```
https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/docs
```

---

## 🔐 Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get tokens |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout user |
| GET | `/auth/me` | Get current user profile |

**Authorization Header:**
```
Authorization: Bearer {accessToken}
```

---

## 👥 Speaker Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/speakers` | Create speaker | ✅ |
| GET | `/speakers` | List speakers (paginated) | ✅ |
| GET | `/speakers/statistics` | Get speaker statistics | ✅ |
| GET | `/speakers/{id}` | Get speaker by ID | ✅ |
| PATCH | `/speakers/{id}` | Update speaker | ✅ |
| PUT | `/speakers/{id}/bucket` | Update speaker bucket | ✅ |
| DELETE | `/speakers/{id}` | Delete speaker (soft) | ✅ |

**Query Parameters for GET /speakers:**
- `page` (number) - Page number
- `limit` (number) - Items per page
- `bucket` (string) - Filter by bucket
- `status` (string) - Filter by status
- `search` (string) - Search by name/email
- `sortBy` (string) - Sort field
- `sortOrder` (string) - asc/desc

---

## 📝 Draft Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/drafts/ingest` | Ingest drafts for speaker | ✅ |
| POST | `/drafts` | Create draft manually | ✅ |
| GET | `/drafts` | List all drafts | ✅ |
| GET | `/drafts/{id}` | Get draft by ID | ✅ |
| GET | `/drafts/speaker/{speakerId}` | Get speaker's drafts | ✅ |

**Query Parameters for GET /drafts:**
- `skip` (number) - Records to skip
- `limit` (number) - Max records
- `draft_type` (string) - Filter by type (AD/LD/IFN)
- `is_processed` (boolean) - Filter by processing status

---

## 🔄 Aggregation Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/speakers/{id}/complete` | Get complete speaker data | ✅ |
| GET | `/dashboard/metrics` | Get dashboard metrics | ✅ |

---

## 🤖 Workflow Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/workflow/generate-dfn` | Generate DFN (AI workflow) | ✅ |

---

## ❤️ Health Check Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | API Gateway health | ❌ |
| GET | `/health/services` | All services health | ✅ |

---

## 📊 Enums & Constants

### Bucket Types
```
EXCELLENT
GOOD
AVERAGE
POOR
NEEDS_IMPROVEMENT
```

### Speaker Status
```
ACTIVE
INACTIVE
PENDING
ARCHIVED
```

### Draft Types
```
AD  - Actual Draft
LD  - Learning Draft
IFN - Initial From Notes
```

### User Roles
```
user
admin
```

---

## 🚨 HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

---

## 💡 Quick Examples

### Login
```bash
curl -X POST https://api-gateway.../api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

### Create Speaker
```bash
curl -X POST https://api-gateway.../api/v1/speakers \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Dr. Smith","bucket":"GOOD","email":"smith@hospital.com"}'
```

### Get Speakers
```bash
curl -X GET "https://api-gateway.../api/v1/speakers?page=1&limit=20" \
  -H "Authorization: Bearer {token}"
```

### Generate DFN
```bash
curl -X POST https://api-gateway.../api/v1/workflow/generate-dfn \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"speakerId":"550e8400-...","prompt":"Generate note","options":{"useLangGraph":true}}'
```

### Health Check
```bash
curl https://api-gateway.../api/v1/health
```

---

## 🔗 Resources

- **Full Documentation**: [FRONTEND_API_DOCUMENTATION.md](./FRONTEND_API_DOCUMENTATION.md)
- **Swagger UI**: https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/docs
- **Health Check**: https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-16  
**Status**: ✅ Production Ready

