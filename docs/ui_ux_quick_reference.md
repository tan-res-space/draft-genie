# DraftGenie UI/UX Quick Reference Guide

**Version:** 1.0  
**Last Updated:** 2025-10-16  
**For:** Frontend Developers

---

## 🎨 Design Tokens Cheat Sheet

### Colors
```css
/* Bucket Colors */
--excellent: #4CAF50    /* 🟢 Green */
--good: #2196F3         /* 🔵 Blue */
--average: #FFC107      /* 🟡 Amber */
--poor: #FF9800         /* 🟠 Orange */
--needs-improvement: #F44336  /* 🔴 Red */

/* Primary */
--primary: #1976D2
--primary-light: #42A5F5
--primary-dark: #1565C0

/* Semantic */
--success: #4CAF50
--warning: #FF9800
--error: #F44336
--info: #2196F3
```

### Spacing
```css
--xs: 4px    --sm: 8px    --md: 16px
--lg: 24px   --xl: 32px   --2xl: 48px   --3xl: 64px
```

### Typography
```css
/* Sizes */
--xs: 12px   --sm: 14px   --md: 16px   --lg: 18px
--xl: 20px   --2xl: 24px  --3xl: 30px  --4xl: 36px

/* Weights */
--regular: 400   --medium: 500   --semibold: 600   --bold: 700
```

---

## 🔌 API Quick Reference

### Base URL
```
https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1
```

### Authentication
```javascript
// Headers
Authorization: Bearer {accessToken}
Content-Type: application/json

// Token Lifetime
Access Token: 24 hours
Refresh Token: 30 days
```

### Key Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| **Login** | POST | `/auth/login` |
| **Refresh Token** | POST | `/auth/refresh` |
| **List Speakers** | GET | `/speakers?page=1&limit=20` |
| **Create Speaker** | POST | `/speakers` |
| **Get Speaker** | GET | `/speakers/{id}` |
| **Update Speaker** | PATCH | `/speakers/{id}` |
| **Update Bucket** | PUT | `/speakers/{id}/bucket` |
| **Get Drafts** | GET | `/drafts/speaker/{id}` |
| **Ingest Drafts** | POST | `/drafts/ingest?speaker_id={id}` |
| **Generate DFN** | POST | `/workflow/generate-dfn` |
| **List Evaluations** | GET | `/evaluations` |
| **Dashboard Metrics** | GET | `/dashboard/metrics` |

---

## 📋 Common Request/Response Examples

### Create Speaker
```javascript
// Request
POST /api/v1/speakers
{
  "name": "Dr. John Smith",
  "email": "john@hospital.com",
  "bucket": "GOOD",
  "externalId": "inst-12345"
}

// Response (201)
{
  "id": "550e8400-...",
  "name": "Dr. John Smith",
  "bucket": "GOOD",
  "status": "ACTIVE",
  "createdAt": "2025-10-16T10:30:00Z"
}
```

### Generate DFN
```javascript
// Request
POST /api/v1/workflow/generate-dfn
{
  "speakerId": "550e8400-...",
  "prompt": "Generate professional medical note",
  "options": {
    "useLangGraph": true,
    "maxTokens": 2000
  }
}

// Response (201) - Takes 10-30 seconds
{
  "workflow": { "status": "completed" },
  "generation": {
    "dfn_text": "Generated note...",
    "confidence": 0.95
  },
  "dfn": {
    "draft_id": "dfn_789012",
    "created_at": "2025-10-16T10:35:00Z"
  }
}
```

---

## 🎯 Component Usage Examples

### BucketBadge
```jsx
// React
<BucketBadge 
  bucket="EXCELLENT" 
  size="md" 
  variant="filled" 
  showIcon={true} 
/>

// Vue
<BucketBadge 
  :bucket="speaker.bucket" 
  size="md" 
  variant="filled" 
  :show-icon="true" 
/>

// Angular
<app-bucket-badge 
  [bucket]="speaker.bucket" 
  size="md" 
  variant="filled" 
  [showIcon]="true">
</app-bucket-badge>
```

### SpeakerCard
```jsx
// React
<SpeakerCard 
  speaker={speaker}
  onClick={handleClick}
  showActions={true}
  variant="default"
/>

// Vue
<SpeakerCard 
  :speaker="speaker"
  @click="handleClick"
  :show-actions="true"
  variant="default"
/>
```

### MetricsPanel
```jsx
// React
<MetricsPanel 
  metrics={{
    ser: 0.15,
    wer: 0.08,
    similarity: 0.92,
    qualityScore: 87.5
  }}
  layout="horizontal"
  showTrends={true}
/>
```

---

## 🔄 State Management Patterns

### Speaker State
```typescript
interface SpeakerState {
  speakers: Speaker[];
  selectedSpeaker: Speaker | null;
  loading: boolean;
  error: string | null;
  filters: {
    bucket?: BucketType;
    status?: SpeakerStatus;
    search?: string;
  };
  pagination: {
    page: number;
    limit: number;
    total: number;
  };
}
```

### API Call Pattern
```typescript
// With loading and error states
async function fetchSpeakers(filters) {
  setState({ loading: true, error: null });
  
  try {
    const response = await apiClient.get('/speakers', { params: filters });
    setState({ 
      speakers: response.data.data,
      pagination: response.data.pagination,
      loading: false 
    });
  } catch (error) {
    setState({ 
      error: error.message,
      loading: false 
    });
  }
}
```

---

## ⚠️ Error Handling

### HTTP Status Codes
| Code | Meaning | UI Action |
|------|---------|-----------|
| 200 | Success | Update UI |
| 201 | Created | Show success toast, redirect |
| 400 | Bad Request | Show validation errors inline |
| 401 | Unauthorized | Refresh token or redirect to login |
| 404 | Not Found | Show "Not found" message |
| 409 | Conflict | Show conflict message |
| 429 | Rate Limit | Show "Too many requests", retry |
| 500 | Server Error | Show error, offer retry |

### Error Display Pattern
```typescript
function handleError(error) {
  if (error.response) {
    switch (error.response.status) {
      case 400:
        // Show validation errors inline
        showValidationErrors(error.response.data.message);
        break;
      case 401:
        // Refresh token or redirect
        refreshTokenOrRedirect();
        break;
      case 404:
        // Show not found message
        showToast('Resource not found', 'error');
        break;
      case 409:
        // Show conflict message
        showToast(error.response.data.message, 'warning');
        break;
      case 429:
        // Rate limit - wait and retry
        showToast('Too many requests. Please wait.', 'warning');
        setTimeout(() => retryRequest(), 2000);
        break;
      default:
        // Generic error
        showToast('An error occurred. Please try again.', 'error');
    }
  } else {
    // Network error
    showToast('Network error. Please check your connection.', 'error');
  }
}
```

---

## 🎨 Loading States

### Skeleton Loader
```html
<!-- For lists -->
<div class="skeleton-card">
  <div class="skeleton-avatar"></div>
  <div class="skeleton-text skeleton-text--title"></div>
  <div class="skeleton-text skeleton-text--subtitle"></div>
</div>
```

### Spinner
```html
<!-- For actions -->
<div class="spinner-container">
  <div class="spinner"></div>
  <p>Loading...</p>
</div>
```

### Progress Bar
```html
<!-- For multi-step workflows -->
<div class="progress-bar">
  <div class="progress-bar__fill" style="width: 66%;"></div>
</div>
<p>Step 2 of 3: Generating with AI...</p>
```

---

## 📱 Responsive Breakpoints

```css
/* Mobile First */
.container {
  padding: 16px;
}

/* Tablet (768px+) */
@media (min-width: 768px) {
  .container {
    padding: 24px;
  }
}

/* Desktop (1024px+) */
@media (min-width: 1024px) {
  .container {
    padding: 32px;
  }
}

/* Large Desktop (1440px+) */
@media (min-width: 1440px) {
  .container {
    padding: 48px;
  }
}
```

---

## ♿ Accessibility Checklist

- [ ] All interactive elements keyboard accessible
- [ ] Logical tab order
- [ ] Visible focus indicators
- [ ] ARIA labels for icons and buttons
- [ ] ARIA live regions for dynamic content
- [ ] Alt text for images
- [ ] Color contrast 4.5:1 minimum
- [ ] Text zoom up to 200% supported
- [ ] Semantic HTML (headings, lists, tables)
- [ ] Screen reader tested

---

## 🧪 Testing Checklist

### Functional
- [ ] Login/logout
- [ ] Create speaker (SSA)
- [ ] Bulk import (BSA)
- [ ] View/edit speaker
- [ ] Generate DFN
- [ ] View evaluations
- [ ] Approve bucket change

### UI/UX
- [ ] Loading states appear
- [ ] Error messages clear
- [ ] Success messages auto-dismiss
- [ ] Forms validate real-time
- [ ] Pagination works
- [ ] Filters apply correctly

### Responsive
- [ ] Mobile (320px-767px)
- [ ] Tablet (768px-1023px)
- [ ] Desktop (1024px+)

### Performance
- [ ] Page load < 3s
- [ ] API calls < 2s (except DFN)
- [ ] Smooth animations (60fps)

---

## 🔧 Development Setup

### Install Dependencies
```bash
# React
npx create-react-app draftgenie-ui
cd draftgenie-ui
npm install axios react-router-dom

# Vue
npm create vue@latest
cd draftgenie-ui
npm install axios vue-router

# Angular
ng new draftgenie-ui
cd draftgenie-ui
npm install axios
```

### Environment Variables
```bash
# .env
REACT_APP_API_BASE_URL=https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1
REACT_APP_API_TIMEOUT=30000
```

### API Client Setup
```javascript
// src/api/client.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle token refresh
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        try {
          const { data } = await axios.post(
            `${process.env.REACT_APP_API_BASE_URL}/auth/refresh`,
            { refreshToken }
          );
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

export default apiClient;
```

---

## 📚 Resources

### Documentation
- **Main Spec:** `docs/ui_ux_design_specification.md`
- **Workflows:** `docs/ui_ux_visual_workflows.md`
- **Components:** `docs/ui_component_specifications.md`
- **API Docs:** `docs/FRONTEND_API_DOCUMENTATION.md`

### Tools
- **Swagger UI:** `/api/docs`
- **Postman:** `docs/DraftGenie_API.postman_collection.json`
- **Health Check:** `/api/v1/health`

### Design
- **Figma:** (Create mockups based on specs)
- **Storybook:** (Component library)
- **Icons:** Material Icons, Font Awesome, or Heroicons

---

## 🚀 Quick Start Workflow

1. **Setup Project**
   ```bash
   npx create-react-app draftgenie-ui
   cd draftgenie-ui
   npm install axios react-router-dom
   ```

2. **Configure API Client**
   - Create `src/api/client.js`
   - Add environment variables
   - Set up interceptors

3. **Test API Connection**
   ```javascript
   // Test health endpoint
   apiClient.get('/health').then(console.log);
   ```

4. **Implement Authentication**
   - Login page
   - Token storage
   - Protected routes

5. **Build Core Components**
   - BucketBadge
   - SpeakerCard
   - MetricsPanel

6. **Create Main Screens**
   - Dashboard
   - Speaker List
   - Speaker Profile

7. **Test & Deploy**
   - Run tests
   - Build production
   - Deploy

---

**Last Updated:** 2025-10-16  
**Status:** ✅ Ready for Development  
**Support:** Check Swagger UI or contact backend team

