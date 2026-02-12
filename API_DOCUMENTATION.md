# Job Matching API - Complete Documentation

Base URL: `http://localhost:8080`

---

## 📋 Table of Contents

1. [Health & Info](#health--info)
2. [Job Matching](#job-matching)
3. [Job Listing](#job-listing)
4. [User Interactions](#user-interactions)
5. [Email Subscriptions](#email-subscriptions)
6. [Admin Operations](#admin-operations)

---

## 🏥 Health & Info

### 1. Root - API Information
Get basic API information.

**Endpoint:** `GET /`

**cURL:**
```bash
curl -X GET "http://localhost:8080/"
```

**Response:**
```json
{
  "message": "Job Matching API",
  "version": "1.0.0",
  "status": "running"
}
```

---

### 2. Health Check
Check API health status.

**Endpoint:** `GET /health`

**cURL:**
```bash
curl -X GET "http://localhost:8080/health"
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-02-12T18:00:00Z"
}
```

---

### 3. Get Engineering Job Types
Get list of available engineering job categories.

**Endpoint:** `GET /types/engineering`

**cURL:**
```bash
curl -X GET "http://localhost:8080/types/engineering"
```

**Response:**
```json
{
  "job_types": [
    "software-engineer-jobs",
    "data-scientist-jobs",
    "machine-learning-engineer-jobs",
    ...
  ]
}
```

---

## 🎯 Job Matching

### 1. Match Resume (Text)
Match jobs based on resume text.

**Endpoint:** `POST /match/resume`

**cURL:**
```bash
curl -X POST "http://localhost:8080/match/resume" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Experienced Software Engineer with 5 years in Python, FastAPI, React. Built scalable microservices and REST APIs.",
    "location": "San Francisco",
    "internship_only": false,
    "job_level": "MID_LEVEL",
    "stipend_min": 100000
  }'
```

**Request Body:**
```json
{
  "resume_text": "Your resume content here...",
  "location": "San Francisco",
  "internship_only": false,
  "job_level": "MID_LEVEL",
  "stipend_min": 100000
}
```

**Response:**
```json
{
  "matches": [
    {
      "id": "job123",
      "title": "Senior Software Engineer",
      "company_display_name": "Tech Corp",
      "location": "San Francisco, CA",
      "salary_min": 120000,
      "salary_max": 180000,
      "match_score": 0.92,
      "redirect_url": "https://...",
      "description": "..."
    }
  ],
  "total_matches": 25,
  "processing_time_ms": 450
}
```

---

### 2. Match Resume (File Upload)
Match jobs based on uploaded resume file.

**Endpoint:** `POST /match/resume/upload`

**cURL:**
```bash
curl -X POST "http://localhost:8080/match/resume/upload?location=New%20York&job_level=SENIOR_LEVEL&stipend_min=120000" \
  -F "file=@/path/to/your/resume.pdf"
```

**Query Parameters:**
- `location` (optional): Preferred location
- `internship_only` (optional): true/false
- `job_level` (optional): ENTRY_LEVEL, MID_LEVEL, SENIOR_LEVEL, EXECUTIVE
- `stipend_min` (optional): Minimum salary

**Supported File Types:** PDF, DOCX, TXT

---

### 3. Match Job Description
Match candidates based on job description.

**Endpoint:** `POST /match/jd`

**cURL:**
```bash
curl -X POST "http://localhost:8080/match/jd" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Looking for a Senior Python Developer with FastAPI experience...",
    "location": "Remote",
    "job_level": "SENIOR_LEVEL"
  }'
```

**Request Body:**
```json
{
  "job_description": "Job description text...",
  "location": "Remote",
  "job_level": "SENIOR_LEVEL"
}
```

---

## 📝 Job Listing

### 1. Get All Jobs
Retrieve all available jobs with pagination.

**Endpoint:** `GET /jobs`

**cURL:**
```bash
curl -X GET "http://localhost:8080/jobs?page=1&page_size=20"
```

**Query Parameters:**
- `page` (default: 1): Page number
- `page_size` (default: 20): Items per page

**Response:**
```json
{
  "jobs": [...],
  "total": 5000,
  "page": 1,
  "page_size": 20,
  "total_pages": 250
}
```

---

### 2. Get Jobs with Filters
Filter jobs by various criteria.

**Endpoint:** `GET /jobs`

**cURL:**
```bash
curl -X GET "http://localhost:8080/jobs?location=San%20Francisco&remote=true&internship=false&min_stipend=80000&max_stipend=150000&page=1&page_size=10"
```

**Query Parameters:**
- `location` (optional): Job location
- `remote` (optional): true/false
- `internship` (optional): true/false
- `min_stipend` (optional): Minimum salary
- `max_stipend` (optional): Maximum salary
- `page` (default: 1): Page number
- `page_size` (default: 20): Items per page

---

### 3. Get Internships Only
Retrieve only internship positions.

**Endpoint:** `GET /jobs`

**cURL:**
```bash
curl -X GET "http://localhost:8080/jobs?internship=true&page=1&page_size=20"
```

---

### 4. Get Jobs by Location
Filter jobs by specific location.

**Endpoint:** `GET /jobs`

**cURL:**
```bash
curl -X GET "http://localhost:8080/jobs?location=Seattle&page=1&page_size=20"
```

---

## 💼 User Interactions

### 1. Add to Favorites
Add a job to user's favorites.

**Endpoint:** `POST /{job_id}/favorite`

**cURL:**
```bash
curl -X POST "http://localhost:8080/job123/favorite" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user@example.com"
  }'
```

**Request Body:**
```json
{
  "user_id": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Job added to favorites",
  "status": "success",
  "is_active": true
}
```

---

### 2. Get User Favorites
Retrieve all favorited jobs for a user.

**Endpoint:** `GET /favorites`

**cURL:**
```bash
curl -X GET "http://localhost:8080/favorites?user_id=user@example.com"
```

**Query Parameters:**
- `user_id` (required): User identifier

**Response:**
```json
{
  "favorites": [
    {
      "id": "job123",
      "title": "Software Engineer",
      "company_display_name": "Tech Corp",
      ...
    }
  ],
  "total": 5
}
```

---

### 3. Add to Bookmarks
Bookmark a job for later review.

**Endpoint:** `POST /{job_id}/bookmark`

**cURL:**
```bash
curl -X POST "http://localhost:8080/job456/bookmark" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user@example.com"
  }'
```

**Request Body:**
```json
{
  "user_id": "user@example.com"
}
```

---

### 4. Get User Bookmarks
Retrieve all bookmarked jobs for a user.

**Endpoint:** `GET /bookmarks`

**cURL:**
```bash
curl -X GET "http://localhost:8080/bookmarks?user_id=user@example.com"
```

**Query Parameters:**
- `user_id` (required): User identifier

---

## 📧 Email Subscriptions

### 1. Subscribe to Job Emails (with Resume Upload)
Subscribe to personalized job alerts by uploading your resume.

**Endpoint:** `POST /subscribe`

**cURL:**
```bash
curl -X POST "http://localhost:8080/subscribe?email=user@example.com&frequency=daily&location=San%20Francisco&job_level=SENIOR_LEVEL&stipend_min=120000&is_enabled=true" \
  -F "file=@/path/to/resume.pdf"
```

**Query Parameters:**
- `email` (required): Email address
- `frequency` (optional, default: biweekly): daily, weekly, biweekly
- `is_enabled` (optional, default: true): Enable/disable notifications
- `location` (optional): Preferred job location
- `internship_only` (optional, default: false): Filter for internships only
- `job_level` (optional): ENTRY_LEVEL, MID_LEVEL, SENIOR_LEVEL, EXECUTIVE
- `stipend_min` (optional): Minimum salary/stipend

**Form Data:**
- `file` (required): Resume file (PDF, DOCX, or TXT)

**Response:**
```json
{
  "message": "Successfully subscribed with resume! You'll receive daily job matches.",
  "status": "success",
  "is_active": true
}
```

---

### 2. Subscribe - Daily Emails
Subscribe with daily frequency.

**cURL:**
```bash
curl -X POST "http://localhost:8080/subscribe?email=user@example.com&frequency=daily" \
  -F "file=@/path/to/resume.pdf"
```

---

### 3. Subscribe - Weekly Emails
Subscribe with weekly frequency.

**cURL:**
```bash
curl -X POST "http://localhost:8080/subscribe?email=user@example.com&frequency=weekly&location=Remote" \
  -F "file=@/path/to/resume.pdf"
```

---

### 4. Subscribe - Bi-weekly Emails (Default)
Subscribe with bi-weekly frequency.

**cURL:**
```bash
curl -X POST "http://localhost:8080/subscribe?email=user@example.com" \
  -F "file=@/path/to/resume.pdf"
```

---

### 5. Update Subscription Preferences
Update existing subscription with new resume and preferences.

**cURL:**
```bash
curl -X POST "http://localhost:8080/subscribe?email=user@example.com&frequency=weekly&location=New%20York&stipend_min=150000" \
  -F "file=@/path/to/updated_resume.pdf"
```

---

### 6. Disable Notifications
Disable email notifications without unsubscribing.

**cURL:**
```bash
curl -X POST "http://localhost:8080/subscribe?email=user@example.com&is_enabled=false" \
  -F "file=@/path/to/resume.pdf"
```

---

### 7. Get All Subscriptions (Admin)
Retrieve all active email subscriptions.

**Endpoint:** `GET /subscriptions`

**cURL:**
```bash
curl -X GET "http://localhost:8080/subscriptions"
```

**Response:**
```json
{
  "subscriptions": [
    {
      "email": "user1@example.com",
      "frequency": "daily",
      "is_enabled": true,
      "location": "San Francisco",
      "job_level": "SENIOR_LEVEL",
      "created_at": "2026-02-10T10:00:00Z"
    },
    {
      "email": "user2@example.com",
      "frequency": "weekly",
      "is_enabled": true,
      "location": "Remote",
      "created_at": "2026-02-11T14:30:00Z"
    }
  ],
  "total": 2
}
```

---

### 8. Unsubscribe
Permanently unsubscribe from job emails.

**Endpoint:** `DELETE /subscribe`

**cURL:**
```bash
curl -X DELETE "http://localhost:8080/subscribe?email=user@example.com"
```

**Query Parameters:**
- `email` (required): Email address to unsubscribe

**Response:**
```json
{
  "message": "Successfully unsubscribed",
  "status": "success"
}
```

---

## 🔧 Admin Operations

### 1. Manual Job Refresh
Manually trigger job database refresh from Adzuna API.

**Endpoint:** `POST /admin/refresh-jobs`

**cURL:**
```bash
curl -X POST "http://localhost:8080/admin/refresh-jobs"
```

**Response:**
```json
{
  "message": "Job refresh triggered successfully",
  "status": "processing"
}
```

---

### 2. Sync Jobs to Google Cloud Talent Solution
Sync jobs to CTS for advanced matching.

**Endpoint:** `POST /admin/sync-to-cts`

**cURL:**
```bash
curl -X POST "http://localhost:8080/admin/sync-to-cts"
```

**Response:**
```json
{
  "message": "CTS sync started",
  "jobs_synced": 1500,
  "status": "success"
}
```

---

### 3. Trigger Personalized Emails - All Subscribers
Manually send personalized job emails to all active subscribers.

**Endpoint:** `POST /admin/trigger-emails`

**cURL:**
```bash
curl -X POST "http://localhost:8080/admin/trigger-emails"
```

**Response:**
```json
{
  "message": "Personalized email delivery triggered for all subscribers",
  "status": "processing"
}
```

---

### 4. Trigger Emails for Specific User
Send personalized job email to a specific subscriber.

**Endpoint:** `POST /admin/trigger-emails`

**cURL:**
```bash
curl -X POST "http://localhost:8080/admin/trigger-emails?email=user@example.com"
```

**Query Parameters:**
- `email` (optional): Specific email address to send to

**Response:**
```json
{
  "message": "Personalized email delivery triggered for user@example.com",
  "status": "processing"
}
```

---

### 5. Clear Cache
Clear application cache (if implemented).

**Endpoint:** `POST /admin/clear-cache`

**cURL:**
```bash
curl -X POST "http://localhost:8080/admin/clear-cache"
```

**Response:**
```json
{
  "message": "Cache cleared successfully",
  "status": "success"
}
```

---

### 6. Get Database Statistics
Get statistics about the job database.

**Endpoint:** `GET /admin/stats`

**cURL:**
```bash
curl -X GET "http://localhost:8080/admin/stats"
```

**Response:**
```json
{
  "total_jobs": 5000,
  "total_subscriptions": 150,
  "active_subscriptions": 142,
  "jobs_added_today": 250,
  "last_refresh": "2026-02-12T03:00:00Z",
  "database_size_mb": 125.5
}
```

---

## 📊 Response Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 201  | Created |
| 400  | Bad Request (invalid parameters) |
| 404  | Not Found |
| 500  | Internal Server Error |

---

## 🔐 Authentication

Currently, the API does not require authentication. For production use, implement:
- API Key authentication
- OAuth 2.0
- JWT tokens

---

## 📝 Notes

### Email Subscription Features:
- **Resume-based matching**: Upload your resume for personalized job recommendations
- **Frequency options**: Choose daily, weekly, or bi-weekly emails
- **Preference filters**: Set location, salary, job level preferences
- **Update anytime**: Re-upload resume or change preferences
- **Pause/Resume**: Disable notifications without losing your subscription

### Scheduled Tasks:
- **Daily Job Refresh**: 3:00 AM (configurable via `JOB_REFRESH_TIME` env var)
- **Daily Email Delivery**: Sent to subscribers with "daily" frequency
- **Weekly Email Delivery**: Sent every Monday to "weekly" subscribers
- **Bi-weekly Email Delivery**: Sent every other Monday to "biweekly" subscribers

### File Upload Limits:
- **Max file size**: 10MB
- **Supported formats**: PDF, DOCX, TXT
- **Resume parsing**: Automatic text extraction from uploaded files

---

## 🚀 Quick Start Examples

### Complete Subscription Flow:
```bash
# 1. Subscribe with resume
curl -X POST "http://localhost:8080/subscribe?email=john@example.com&frequency=daily&location=San%20Francisco&job_level=SENIOR_LEVEL&stipend_min=120000" \
  -F "file=@john_resume.pdf"

# 2. Check subscription (admin)
curl -X GET "http://localhost:8080/subscriptions"

# 3. Manually trigger email for testing
curl -X POST "http://localhost:8080/admin/trigger-emails?email=john@example.com"

# 4. Update preferences later
curl -X POST "http://localhost:8080/subscribe?email=john@example.com&frequency=weekly&stipend_min=150000" \
  -F "file=@john_updated_resume.pdf"

# 5. Unsubscribe
curl -X DELETE "http://localhost:8080/subscribe?email=john@example.com"
```

### Job Search Flow:
```bash
# 1. Upload resume and get matches
curl -X POST "http://localhost:8080/match/resume/upload?location=Remote&job_level=MID_LEVEL" \
  -F "file=@resume.pdf"

# 2. Browse all jobs
curl -X GET "http://localhost:8080/jobs?page=1&page_size=20"

# 3. Filter for specific criteria
curl -X GET "http://localhost:8080/jobs?location=New%20York&remote=true&min_stipend=100000"

# 4. Save favorite jobs
curl -X POST "http://localhost:8080/job123/favorite" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user@example.com"}'

# 5. Get all favorites
curl -X GET "http://localhost:8080/favorites?user_id=user@example.com"
```

---

## 📧 Contact & Support

For issues or questions, please contact the development team.

**API Version:** 1.0.0  
**Last Updated:** February 12, 2026
