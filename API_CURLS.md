# API Curl Documentation

This file contains all available API endpoints and their corresponding `curl` commands for quick testing.

## Base URL
```bash
http://localhost:8000
```

---

## 1. System Health
### Health Check
Check if the API and its dependent services (MongoDB, Google CTS) are healthy.
```bash
curl -X GET http://localhost:8000/health
```
**Full Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-20T20:55:00Z",
  "database": "connected",
  "cts_connection": "healthy",
  "version": "1.0.0"
}
```

### Root Info
Get basic service information and list of main endpoints.
```bash
curl -X GET http://localhost:8000/
```
**Full Response:**
```json
{
  "message": "Welcome to the Job Matching API",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "jobs": "/jobs",
    "match": "/match/resume",
    "admin": "/admin/stats"
  }
}
```

---

## 2. Job Matching
### Match by Resume Text
Submit resume text to find matching jobs.
```bash
curl -X POST http://localhost:8000/match/resume \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Python developer with experience in FastAPI, MongoDB, and AWS. 5 years of backend engineering.",
    "location": "Remote",
    "job_level": "MID_LEVEL"
  }'
```
**Full Response:**
```json
{
  "total_matches": 1,
  "search_time_ms": 125.4,
  "jobs": [
    {
      "job_id": "69987b7ef0d8faf4cdc83809",
      "adzuna_id": "5637855679",
      "title": "Senior Software Engineer",
      "company": "Endian AI",
      "location": "Hyderabad, Telangana",
      "employment_type": "FULL_TIME",
      "salary_min": null,
      "salary_max": null,
      "description": "About Us Endian AI is a forward-thinking technology company...",
      "redirect_url": "https://www.adzuna.in/land/ad/5637855679...",
      "relevance_score": 0.92,
      "is_internship": false
    }
  ],
  "metadata": {
    "location": "Remote",
    "internship_only": false,
    "job_level": "MID_LEVEL"
  }
}
```

### Match by Resume File
Upload a PDF, DOCX, or TXT file to find matching jobs.
```bash
curl -X POST http://localhost:8000/match/resume/upload \
  -F "file=@/path/to/your/resume.pdf"
```

### Match by Job Description (JD)
Find similar jobs based on a job description text.
```bash
curl -X POST http://localhost:8000/match/jd \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "We need a Senior Python Engineer for a high-traffic e-commerce platform.",
    "location": "San Francisco",
    "job_type": "FULL_TIME"
  }'
```

---

## 3. Job Listings & Information
### Get All Jobs (Paginated)
```bash
curl -X GET "http://localhost:8000/jobs?limit=10&skip=0"
```
**Full Response:**
```json
{
  "total": 7268,
  "jobs": [
    {
      "job_id": "69987b7ef0d8faf4cdc83809",
      "adzuna_id": "5637855679",
      "title": "Senior Software Engineer",
      "company": "Endian AI",
      "location": "Hyderabad, Telangana",
      "employment_type": "FULL_TIME",
      "salary_min": null,
      "salary_max": null,
      "description": "About Us...",
      "redirect_url": "https://...",
      "relevance_score": 0.0,
      "is_internship": false
    }
  ]
}
```

### Filter Jobs (Internships)
```bash
curl -X GET "http://localhost:8000/jobs?internship=true&limit=5"
```

### Filter Jobs (Remote & Salary)
```bash
curl -X GET "http://localhost:8000/jobs?remote=true&min_stipend=100000"
```

### Filter Jobs (by Country)
```bash
curl -X GET "http://localhost:8000/jobs?country=India&limit=5"
```
**Full Response:**
```json
{
  "total": 100,
  "jobs": [
    {
      "job_id": "69987b7ef0d8faf4cdc83809",
      "adzuna_id": "5637855679",
      "title": "Senior Software Engineer",
      "company": "Endian AI",
      "location": "Hyderabad, Telangana",
      "employment_type": "FULL_TIME",
      "description": "About Us Endian AI is a forward-thinking technology company...",
      "redirect_url": "https://www.adzuna.in/land/ad/5637855679...",
      "relevance_score": 0.0,
      "is_internship": false
    }
  ]
}
```

### List Engineering Job Types
Get a list of all engineering categories/types found in the database.
```bash
curl -X GET http://localhost:8000/jobs/engineering-types
```

### List Job Locations
Get all unique countries where jobs are currently indexed.
```bash
curl -X GET http://localhost:8000/jobs/locations
```
**Full Response:**
```json
{
  "locations": ["Australia", "Canada", "India", "UK", "US"]
}
```

---

## 4. User Interactions
### Toggle Favorite
Add or remove a job from user's favorites.
```bash
curl -X POST http://localhost:8000/69987b7ef0d8faf4cdc83809/favorite \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123"
  }'
```
**Response Example:**
```json
{
  "message": "Job added to favorites",
  "status": "success",
  "is_active": true
}
```

### Toggle Bookmark
Add or remove a job from user's bookmarks.
```bash
curl -X POST http://localhost:8000/69987b7ef0d8faf4cdc83809/bookmark \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123"
  }'
```

### Get User Favorites
```bash
curl -X GET "http://localhost:8000/favorites?user_id=user_123"
```

### Get User Bookmarks
```bash
curl -X GET "http://localhost:8000/bookmarks?user_id=user_123"
```

---

## 5. Email Subscriptions
### Subscribe for Alerts
Subscribe for automated job matching emails by uploading a resume.
```bash
curl -X POST "http://localhost:8000/subscribe?email=user@example.com&frequency=weekly&location=Remote&internship_only=false" \
  -F "file=@/path/to/your/resume.pdf"
```
**Full Response:**
```json
{
  "message": "Successfully subscribed with resume! You'll receive weekly job matches.",
  "status": "success",
  "is_active": true
}
```
**Parameters:**
- `email`: User email address
- `file`: Resume file (Multipart)
- `frequency`: daily, weekly, or biweekly
- `location`: Preferred location filter

### Unsubscribe
```bash
curl -X DELETE "http://localhost:8000/subscribe?email=user@example.com"
```

---

## 6. Admin & Maintenance
### Manual Job Refresh (Multi-Region)
Trigger a sync of jobs across multiple regions (US, India, GB, CA, AU).
```bash
curl -X POST http://localhost:8000/admin/refresh-jobs-multi-region
```
**Full Response:**
```json
{
  "message": "Multi-region job refresh initiated successfully",
  "sync_id": 0,
  "status": "in_progress"
}
```

### Manual Job Refresh (Single Query/Country)
```bash
curl -X POST "http://localhost:8000/admin/refresh-jobs?search_query=Software%20Engineer&country=in&max_pages=2"
```
**Full Response:**
```json
{
  "message": "Job refresh for 'Software Engineer' initiated successfully",
  "sync_id": 0,
  "status": "in_progress"
}
```

### Force Expire Old Jobs
```bash
curl -X POST http://localhost:8000/admin/expire-jobs
```

### Clear Search Cache
```bash
curl -X POST http://localhost:8000/admin/clear-cache
```

### Database Stats
```bash
curl -X GET http://localhost:8000/admin/stats
```
**Response Example:**
```json
{
  "total_jobs": 7268,
  "active_jobs": 7268,
  "cached_searches": 16
}
```

## 7. Common Response Formats
### Job Object
Standard job format used in most listings and matches.
```json
{
  "job_id": "69987b7ef0d8faf4cdc83809",
  "adzuna_id": "5637855679",
  "title": "Senior Software Engineer",
  "company": "Endian AI",
  "location": "Hyderabad, Telangana",
  "employment_type": "FULL_TIME",
  "description": "Shortened description...",
  "salary_min": null,
  "salary_max": null,
  "redirect_url": "https://...",
  "relevance_score": 0.85,
  "is_internship": false
}
```

### List Response
```json
{
  "total": 100,
  "jobs": [...]
}
```

---

## Interactive Docs
For a full interactive playground, visit:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
