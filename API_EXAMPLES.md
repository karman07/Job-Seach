# API Usage Examples

Complete reference for all endpoints with curl examples.

## Base URL
```
http://localhost:8000
```

---

## 1. Health Check

Check if the API is running and all services are healthy.

### Request
```bash
curl -X GET http://localhost:8000/health
```

### Response
```json
{
  "status": "healthy",
  "timestamp": "2026-02-06T15:30:00",
  "database": "healthy",
  "cts_connection": "healthy",
  "version": "1.0.0"
}
```

---

## 2. Root Endpoint

Get API information and available endpoints.

### Request
```bash
curl -X GET http://localhost:8000/
```

### Response
```json
{
  "service": "Job Matching API",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "resume_matching": "POST /match/resume",
    "resume_upload_matching": "POST /match/resume/upload",
    "jd_matching": "POST /match/jd",
    "job_listing": "GET /jobs",
    "manual_refresh": "POST /admin/refresh-jobs",
    "health": "GET /health"
  }
}
```

---

## 3. Resume Matching

Match a resume to relevant jobs with AI-powered relevance scoring.

### Request - Full Example
```bash
curl -X POST http://localhost:8000/match/resume \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Experienced Software Engineer with 5 years of Python development. Skilled in FastAPI, Django, PostgreSQL, AWS, and Docker. Built and deployed scalable microservices. Strong background in REST APIs and cloud architecture.",
    "location": "San Francisco, CA",
    "internship_only": false,
    "job_level": "MID_LEVEL",
    "stipend_min": 100000
  }'
```

### Request - Minimal (Required Fields Only)
```bash
curl -X POST http://localhost:8000/match/resume \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Python developer with FastAPI and PostgreSQL experience. 3 years in backend development."
  }'
```

### Request - Internship Only
```bash
curl -X POST http://localhost:8000/match/resume \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Computer Science student graduating in 2027. Coursework in Python, Data Structures, and Algorithms. Personal projects using Flask and SQLite.",
    "internship_only": true,
    "location": "Remote"
  }'
```

### Response
```json
{
  "total_matches": 15,
  "search_time_ms": 456.2,
  "jobs": [
    {
      "job_id": 123,
      "adzuna_id": "4567890",
      "title": "Senior Backend Engineer - Python",
      "company": "Tech Innovations Inc",
      "location": "San Francisco, CA",
      "employment_type": "FULL_TIME",
      "salary_min": 140000,
      "salary_max": 180000,
      "description": "We are seeking a talented Backend Engineer...",
      "redirect_url": "https://adzuna.com/job/...",
      "relevance_score": 0.95,
      "is_internship": false
    },
    {
      "job_id": 124,
      "adzuna_id": "4567891",
      "title": "Python Developer - Cloud Infrastructure",
      "company": "CloudScale Systems",
      "location": "San Francisco, CA",
      "employment_type": "FULL_TIME",
      "salary_min": 120000,
      "salary_max": 160000,
      "description": "Join our team building cloud-native applications...",
      "redirect_url": "https://adzuna.com/job/...",
      "relevance_score": 0.88,
      "is_internship": false
    }
  ],
  "metadata": {
    "location": "San Francisco, CA",
    "internship_only": false,
    "job_level": "MID_LEVEL"
  }
}
```

---

## 4. Resume File Upload Matching

Upload a resume file (PDF, DOCX, or TXT) and get matched jobs automatically.

### Request - Using curl with file upload
```bash
# Basic file upload
curl -X POST http://localhost:8000/match/resume/upload \
  -F "file=@/path/to/your/resume.pdf"

# With optional filters
curl -X POST "http://localhost:8000/match/resume/upload?location=New%20York&internship_only=false&job_level=ENTRY_LEVEL&stipend_min=80000" \
  -F "file=@/path/to/your/resume.pdf"

# Upload DOCX resume
curl -X POST http://localhost:8000/match/resume/upload \
  -F "file=@/path/to/resume.docx"

# Upload TXT resume with location filter
curl -X POST "http://localhost:8000/match/resume/upload?location=Remote" \
  -F "file=@/path/to/resume.txt"
```

### Request - Using Python with requests
```python
import requests

# Basic upload
with open('resume.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/match/resume/upload',
        files=files
    )
    print(response.json())

# With filters
with open('resume.pdf', 'rb') as f:
    files = {'file': f}
    params = {
        'location': 'San Francisco',
        'internship_only': False,
        'job_level': 'MID_LEVEL',
        'stipend_min': 100000
    }
    response = requests.post(
        'http://localhost:8000/match/resume/upload',
        files=files,
        params=params
    )
    print(response.json())
```

### Supported File Formats
- **PDF** (.pdf)
- **Word Document** (.docx)
- **Plain Text** (.txt)

### File Requirements
- Maximum file size: 10MB
- Minimum content: 50 characters
- File must be a valid resume with readable text

### Query Parameters
- `location` (optional): Preferred job location (e.g., "San Francisco, CA", "Remote")
- `internship_only` (optional): Filter for internships only (true/false, default: false)
- `job_level` (optional): Preferred job level (ENTRY_LEVEL, MID_LEVEL, SENIOR_LEVEL, EXECUTIVE)
- `stipend_min` (optional): Minimum salary/stipend in USD

### Response
```json
{
  "total_matches": 12,
  "search_time_ms": 523.8,
  "jobs": [
    {
      "job_id": "65f1a2b3c4d5e6f7g8h9i0j1",
      "adzuna_id": "4567890",
      "title": "Software Engineer - Python",
      "company": "Innovation Labs",
      "location": "San Francisco, CA",
      "employment_type": "FULL_TIME",
      "salary_min": 110000,
      "salary_max": 150000,
      "description": "Looking for a talented Python developer...",
      "redirect_url": "https://adzuna.com/job/...",
      "relevance_score": 0.92,
      "is_internship": false
    }
  ],
  "metadata": {
    "filename": "resume.pdf",
    "file_type": "application/pdf",
    "location": "San Francisco, CA",
    "internship_only": false,
    "job_level": "MID_LEVEL",
    "stipend_min": 100000
  }
}
```

### Error Responses

**Invalid file format:**
```json
{
  "detail": "Invalid file extension. Allowed: .pdf, .docx, .txt"
}
```

**File too large:**
```json
{
  "detail": "File too large. Maximum size is 10.0MB"
}
```

**Empty or invalid resume:**
```json
{
  "detail": "Resume text is too short or empty. Please upload a valid resume with at least 50 characters."
}
```

---

## 5. Job Description Matching

Find similar jobs based on a job description.

### Request
```bash
curl -X POST http://localhost:8000/match/jd \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "We are looking for a Python Backend Developer with expertise in FastAPI and microservices. The ideal candidate will have experience with PostgreSQL, Redis, Docker, and AWS. You will be responsible for designing and implementing RESTful APIs, optimizing database queries, and deploying applications to the cloud.",
    "location": "New York",
    "job_type": "FULL_TIME"
  }'
```

### Request - Minimal
```bash
curl -X POST http://localhost:8000/match/jd \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Looking for a data scientist with Python and machine learning experience. Must know pandas, scikit-learn, and TensorFlow."
  }'
```

### Response
```json
{
  "total_matches": 12,
  "search_time_ms": 389.1,
  "jobs": [
    {
      "job_id": 456,
      "adzuna_id": "7890123",
      "title": "Backend Python Engineer",
      "company": "StartupXYZ",
      "location": "New York, NY",
      "employment_type": "FULL_TIME",
      "salary_min": 110000,
      "salary_max": 150000,
      "description": "FastAPI, PostgreSQL, Docker...",
      "redirect_url": "https://adzuna.com/job/...",
      "relevance_score": 0.92,
      "is_internship": false
    }
  ],
  "metadata": {
    "location": "New York",
    "job_type": "FULL_TIME"
  }
}
```

---

## 6. Job Listing with Filters

Get paginated job listings with optional filters.

### Request - No Filters
```bash
curl -X GET "http://localhost:8000/jobs?limit=10"
```

### Request - Internships Only
```bash
curl -X GET "http://localhost:8000/jobs?internship=true&limit=20"
```

### Request - Remote Jobs with Salary Filter
```bash
curl -X GET "http://localhost:8000/jobs?remote=true&min_stipend=80000&max_stipend=150000"
```

### Request - Location + Full-time
```bash
curl -X GET "http://localhost:8000/jobs?location=Seattle&internship=false&limit=15"
```

### Request - With Pagination
```bash
curl -X GET "http://localhost:8000/jobs?skip=20&limit=10"
```

### Query Parameters
- `min_stipend` (float): Minimum salary
- `max_stipend` (float): Maximum salary
- `remote` (boolean): Filter remote jobs
- `internship` (boolean): Filter internships
- `location` (string): Location keyword (partial match)
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Results per page (default: 50, max: 100)

### Response
```json
{
  "total": 145,
  "jobs": [
    {
      "job_id": 789,
      "adzuna_id": "1234567",
      "title": "Software Engineering Intern",
      "company": "Google",
      "location": "Mountain View, CA",
      "employment_type": "INTERNSHIP",
      "salary_min": 7000,
      "salary_max": 9000,
      "description": "Join our team for summer 2027...",
      "redirect_url": "https://adzuna.com/job/...",
      "relevance_score": 0.0,
      "is_internship": true
    }
  ]
}
```

---

## 7. Manual Job Refresh (Admin)

Trigger an immediate job sync from Adzuna (runs in background).

### Request
```bash
curl -X POST http://localhost:8000/admin/refresh-jobs
```

### Response
```json
{
  "message": "Job refresh initiated successfully",
  "sync_id": 0,
  "status": "in_progress"
}
```

### Using Celery (if workers running)
```bash
curl -X POST http://localhost:8000/admin/refresh-jobs-celery
```

### Response
```json
{
  "message": "Job refresh queued in Celery",
  "sync_id": 0,
  "status": "queued"
}
```

---

## Interactive API Documentation

FastAPI provides built-in interactive documentation:

### Swagger UI
```
http://localhost:8000/docs
```

### ReDoc
```
http://localhost:8000/redoc
```

---

## Error Responses

### 400 Bad Request - Invalid Input
```bash
curl -X POST http://localhost:8000/match/resume \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Too short"
  }'
```

```json
{
  "detail": [
    {
      "loc": ["body", "resume_text"],
      "msg": "Resume text must be at least 50 characters",
      "type": "value_error"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Matching failed: Connection timeout"
}
```

---

## Python Examples

### Using requests library

```python
import requests

# Resume matching
response = requests.post(
    "http://localhost:8000/match/resume",
    json={
        "resume_text": "Your resume text here...",
        "location": "Austin, TX",
        "job_level": "SENIOR_LEVEL"
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Found {data['total_matches']} matches")
    
    for job in data['jobs'][:5]:
        print(f"{job['title']} at {job['company']}")
        print(f"Score: {job['relevance_score']:.2f}")
else:
    print(f"Error: {response.status_code}")
```

### Using httpx (async)

```python
import httpx
import asyncio

async def match_resume():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/match/resume",
            json={
                "resume_text": "Your resume text...",
                "internship_only": True
            }
        )
        return response.json()

# Run async function
result = asyncio.run(match_resume())
print(result)
```

---

## JavaScript/TypeScript Examples

### Using fetch

```javascript
// Resume matching
const matchResume = async (resumeText) => {
  const response = await fetch('http://localhost:8000/match/resume', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      resume_text: resumeText,
      location: 'Boston',
      job_level: 'ENTRY_LEVEL'
    })
  });
  
  const data = await response.json();
  console.log(`Found ${data.total_matches} jobs`);
  return data.jobs;
};

// Get jobs with filters
const getJobs = async () => {
  const params = new URLSearchParams({
    internship: 'true',
    remote: 'true',
    limit: '20'
  });
  
  const response = await fetch(`http://localhost:8000/jobs?${params}`);
  const data = await response.json();
  return data.jobs;
};
```

### Using axios

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Match resume
const matchResume = async (resumeText, filters = {}) => {
  try {
    const response = await api.post('/match/resume', {
      resume_text: resumeText,
      ...filters
    });
    return response.data;
  } catch (error) {
    console.error('Matching failed:', error.response.data);
    throw error;
  }
};

// Get jobs
const getJobs = async (filters = {}) => {
  const response = await api.get('/jobs', { params: filters });
  return response.data;
};
```

---

## Testing Workflow

### 1. Check Service Health
```bash
curl http://localhost:8000/health
```

### 2. Trigger Initial Job Sync
```bash
curl -X POST http://localhost:8000/admin/refresh-jobs
# Wait a few minutes for jobs to be fetched
```

### 3. List Available Jobs
```bash
curl "http://localhost:8000/jobs?limit=5"
```

### 4. Test Resume Matching
```bash
curl -X POST http://localhost:8000/match/resume \
  -H "Content-Type: application/json" \
  -d @sample_resume.json
```

### 5. Test JD Matching
```bash
curl -X POST http://localhost:8000/match/jd \
  -H "Content-Type: application/json" \
  -d @sample_jd.json
```

---

## Rate Limiting (Future)

When rate limiting is implemented:

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60,
  "limit": 100,
  "remaining": 0
}
```

Headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1612345678
```
