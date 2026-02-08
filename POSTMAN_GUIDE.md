# Postman Collection - Job Matching API

## Files Included

1. **Job_Matching_API.postman_collection.json** - Complete API collection
2. **Job_Matching_API_Local.postman_environment.json** - Local environment (localhost:8000)
3. **Job_Matching_API_Production.postman_environment.json** - Production environment (VM)

## Import to Postman

### Method 1: Import Files
1. Open Postman
2. Click **Import** button (top left)
3. Drag and drop all 3 JSON files
4. Click **Import**

### Method 2: Import from File
1. Open Postman
2. Click **Import** → **Choose Files**
3. Select the collection and environment files
4. Click **Open**

## Setup Environment

1. Click **Environments** in left sidebar
2. Select **Job Matching API - Local** for local testing
3. Or select **Job Matching API - Production** for VM testing
4. Update `base_url` in Production environment with your VM IP

## API Endpoints Overview

### 1. Health & Info (2 endpoints)
- `GET /` - API information
- `GET /health` - Health check

### 2. Job Matching (3 endpoints)
- `POST /match/resume` - Match resume to jobs
- `POST /match/resume` - Match resume (internship variant)
- `POST /match/jd` - Match job description

### 3. Job Listing (5 endpoints)
- `GET /jobs` - Get all jobs
- `GET /jobs?filters` - Get jobs with filters
- `GET /jobs?internship=true` - Get internships only
- `GET /jobs?location=X` - Get jobs by location
- `GET /jobs?skip=X&limit=Y` - Pagination

### 4. Admin (4 endpoints)
- `POST /admin/refresh-jobs` - Manual job refresh
- `POST /admin/sync-to-cts` - Sync to Google CTS
- `POST /admin/clear-cache` - Clear cache
- `GET /admin/stats` - Get statistics

## Quick Test Flow

### 1. Check API Health
```
GET {{base_url}}/health
```

### 2. Get API Info
```
GET {{base_url}}/
```

### 3. List Jobs
```
GET {{base_url}}/jobs?limit=10
```

### 4. Match Resume
```
POST {{base_url}}/match/resume
Body: {
  "resume_text": "Your resume text here (min 50 chars)",
  "location": "San Francisco, CA",
  "job_level": "SENIOR_LEVEL",
  "stipend_min": 80000
}
```

### 5. Get Internships
```
GET {{base_url}}/jobs?internship=true&limit=20
```

## Request Examples

### Resume Matching - Full Example
```json
POST /match/resume
{
  "resume_text": "Experienced Software Engineer with 5 years in Python, FastAPI, and cloud technologies. Skilled in building scalable APIs, microservices, and working with AWS and GCP. Strong background in MongoDB, PostgreSQL, and Docker. Looking for senior backend engineer roles.",
  "location": "San Francisco, CA",
  "internship_only": false,
  "job_level": "SENIOR_LEVEL",
  "stipend_min": 100000
}
```

### Job Description Matching
```json
POST /match/jd
{
  "job_description": "We are looking for a Senior Backend Engineer to join our team. You will be responsible for designing and implementing scalable APIs using Python and FastAPI. Experience with cloud platforms (AWS/GCP), Docker, and MongoDB is required.",
  "location": "New York, NY",
  "job_type": "FULL_TIME"
}
```

### Job Filters
```
GET /jobs?min_stipend=50000&max_stipend=150000&remote=true&limit=50
```

## Response Examples

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "database": "healthy",
  "cts_connection": "healthy",
  "version": "1.0.0"
}
```

### Match Result Response
```json
{
  "total_matches": 25,
  "search_time_ms": 450.2,
  "jobs": [
    {
      "job_id": "507f1f77bcf86cd799439011",
      "adzuna_id": "12345678",
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "employment_type": "FULL_TIME",
      "salary_min": 120000,
      "salary_max": 180000,
      "description": "Job description...",
      "redirect_url": "https://...",
      "relevance_score": 0.95,
      "is_internship": false
    }
  ],
  "metadata": {
    "location": "San Francisco, CA",
    "job_level": "SENIOR_LEVEL"
  }
}
```

## Query Parameters

### GET /jobs
- `min_stipend` (float) - Minimum salary
- `max_stipend` (float) - Maximum salary
- `remote` (boolean) - Remote jobs only
- `internship` (boolean) - Internships only
- `location` (string) - Location filter
- `skip` (int) - Pagination offset
- `limit` (int) - Results per page (max 100)

## Job Levels
- `ENTRY_LEVEL`
- `MID_LEVEL`
- `SENIOR_LEVEL`
- `EXECUTIVE`

## Employment Types
- `FULL_TIME`
- `PART_TIME`
- `CONTRACTOR`
- `INTERNSHIP`

## Testing Tips

1. **Start with health check** to ensure API is running
2. **Use local environment** for development
3. **Switch to production** when testing on VM
4. **Save responses** as examples in Postman
5. **Use variables** for dynamic values
6. **Create test scripts** for automated testing

## Troubleshooting

### Connection Refused
- Check if API is running: `docker ps`
- Verify port 8000 is accessible
- Check firewall rules

### 422 Validation Error
- Ensure resume_text is at least 50 characters
- Check required fields are provided
- Verify enum values (JobLevel, EmploymentType)

### 500 Internal Server Error
- Check API logs: `docker logs -f jobmatch_api`
- Verify MongoDB connection
- Check CTS credentials

## Advanced Usage

### Run Collection with Newman (CLI)
```bash
npm install -g newman
newman run Job_Matching_API.postman_collection.json \
  -e Job_Matching_API_Local.postman_environment.json
```

### Export Results
```bash
newman run Job_Matching_API.postman_collection.json \
  -e Job_Matching_API_Local.postman_environment.json \
  --reporters cli,json \
  --reporter-json-export results.json
```

## API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
