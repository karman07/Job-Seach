# Job Matching Backend API

Production-grade job matching backend that fetches jobs from Adzuna, stores them in PostgreSQL, syncs to Google Cloud Talent Solution, and matches resumes with relevant jobs.

## Architecture

```
┌─────────────────┐
│   Frontend      │
│   (Any Client)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         FastAPI Application                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Jobs    │  │ Matching │  │  Admin   │  │
│  │ Endpoint │  │ Endpoint │  │ Endpoint │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└────────┬────────────────────────────┬───────┘
         │                            │
         ▼                            ▼
┌─────────────────┐         ┌──────────────────┐
│   PostgreSQL    │         │   Redis Cache    │
│   - Jobs        │         │   - Search Cache │
│   - Companies   │         └──────────────────┘
│   - Sync Logs   │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│     Background Processing Layer              │
│  ┌────────────────┐    ┌──────────────────┐  │
│  │  APScheduler   │    │  Celery Workers  │  │
│  │  Daily Refresh │    │  (Optional)      │  │
│  └────────────────┘    └──────────────────┘  │
└──────────────────────────────────────────────┘
         │                        │
         ▼                        ▼
┌────────────────┐      ┌─────────────────────┐
│  Adzuna API    │      │ Google Cloud        │
│  (Job Source)  │      │ Talent Solution     │
└────────────────┘      │ (Matching Engine)   │
                        └─────────────────────┘
```

## Features

- 🔄 **Automated Daily Job Refresh** - Configurable scheduled sync from Adzuna
- 🎯 **AI-Powered Matching** - Google Cloud Talent Solution for intelligent job matching
- 📊 **Resume Matching** - Match resumes to best-fit jobs with relevance scoring
- 🔍 **Job Description Matching** - Find similar jobs based on JD text
- 💰 **Flexible Filtering** - Filter by salary, location, remote, internship, etc.
- 🚀 **Production-Ready** - Error handling, retries, caching, logging
- 📈 **Scalable** - Designed to handle 5k → 50k+ jobs/day

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Job Queue**: Celery (optional) / APScheduler
- **Cloud**: Google Cloud Talent Solution
- **Job Source**: Adzuna API

## Project Structure

```
job_arch/
├── app/
│   ├── api/              # API endpoints
│   │   ├── jobs.py       # Job matching endpoints
│   │   ├── admin.py      # Admin endpoints
│   │   └── health.py     # Health check
│   ├── integrations/     # External service integrations
│   │   ├── adzuna.py     # Adzuna API client
│   │   └── cts.py        # Google CTS client
│   ├── services/         # Business logic
│   │   ├── job_service.py      # Job CRUD & sync
│   │   └── matching_service.py # Matching logic
│   ├── config.py         # Configuration
│   ├── database.py       # Database setup
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── scheduler.py      # APScheduler setup
│   ├── tasks.py          # Celery tasks
│   └── main.py           # FastAPI app
├── alembic/              # Database migrations
├── .env.example          # Environment variables template
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker image
├── docker-compose.yml    # Multi-container setup
└── README.md             # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Google Cloud Project with Talent Solution API enabled
- Adzuna API credentials

### 2. Clone and Install

```bash
cd job_arch
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Adzuna API
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
ADZUNA_COUNTRY=us
ADZUNA_RESULTS_PER_PAGE=50

# Google Cloud
GCP_PROJECT_ID=your-project-id
GCP_TENANT_ID=your-tenant-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
CTS_COMPANY_NAME=projects/your-project/tenants/your-tenant/companies/your-company

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/jobmatch_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Job Refresh (HH:MM format, 24-hour)
JOB_REFRESH_TIME=03:00
JOB_EXPIRY_DAYS=30
```

### 4. Initialize Database

```bash
# Using Alembic (recommended)
alembic upgrade head

# Or direct initialization
python -c "from app.database import init_db; init_db()"
```

### 5. Run the Application

**Option A: Development (single process with APScheduler)**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option B: Production (with Celery workers)**
```bash
# Terminal 1: Run API
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Run Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 3: Run Celery beat (scheduler)
celery -A app.tasks.celery_app beat --loglevel=info
```

**Option C: Docker Compose (all services)**
```bash
docker-compose up --build
```

## API Endpoints

### 1. Resume Matching
```http
POST /match/resume
Content-Type: application/json

{
  "resume_text": "Full resume text here...",
  "location": "San Francisco, CA",
  "internship_only": false,
  "job_level": "MID_LEVEL",
  "stipend_min": 80000
}
```

**Response:**
```json
{
  "total_matches": 25,
  "search_time_ms": 450.2,
  "jobs": [
    {
      "job_id": 123,
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "salary_min": 120000,
      "salary_max": 180000,
      "relevance_score": 0.95,
      "is_internship": false,
      "redirect_url": "https://..."
    }
  ]
}
```

### 2. Job Description Matching
```http
POST /match/jd
Content-Type: application/json

{
  "job_description": "We are looking for a Python developer...",
  "location": "Remote",
  "job_type": "FULL_TIME"
}
```

### 3. Job Listing with Filters
```http
GET /jobs?min_stipend=50000&internship=true&remote=true&limit=20
```

### 4. Manual Job Refresh (Admin)
```http
POST /admin/refresh-jobs
```

### 5. Health Check
```http
GET /health
```

## Scheduler Configuration

The system supports two approaches for scheduled job refresh:

### APScheduler (Default, Simpler)
- Runs in-process with FastAPI
- Configured via `JOB_REFRESH_TIME` in `.env`
- Automatically starts with the application
- Good for: Single-server deployments, development

### Celery Beat (Production, More Robust)
- Separate worker processes
- Better for distributed systems
- Handles failures and retries
- Good for: Multi-server deployments, high availability

## Daily Job Refresh Flow

1. **Trigger**: Runs daily at `JOB_REFRESH_TIME` (default: 3:00 AM)
2. **Fetch**: Queries Adzuna API for recent jobs (last 30 days)
3. **Parse**: Normalizes job data and determines job type/level
4. **Sync DB**: Creates new jobs or updates existing ones
5. **Sync CTS**: Uploads/updates jobs in Google Cloud Talent Solution
6. **Expire**: Marks jobs older than `JOB_EXPIRY_DAYS` as expired
7. **Log**: Records sync statistics in `job_sync_logs` table

## Error Handling & Retries

- **Adzuna API**: 3 retries with exponential backoff
- **CTS API**: 3 retries with exponential backoff
- **Database**: Connection pooling with auto-reconnect
- **Celery**: Automatic task retries on failure
- **Logging**: Comprehensive error logging to files and console

## Scaling Strategy

### 5k → 50k jobs/day

1. **Database Optimization**
   - Indexed columns: `adzuna_id`, `requisition_id`, `status`, `expires_at`
   - Connection pooling (10 base, 20 max overflow)
   - Periodic VACUUM and ANALYZE

2. **API Optimization**
   - Resume search caching (24-hour TTL)
   - Pagination for large result sets
   - Async I/O for external services

3. **CTS Optimization**
   - Batch job uploads (100 jobs at a time)
   - Rate limit handling with retries
   - Incremental updates instead of full re-sync

4. **Background Processing**
   - Celery workers for parallel job processing
   - Multiple worker instances for horizontal scaling
   - Priority queues for critical tasks

5. **Infrastructure**
   - Load balancer for multiple API instances
   - Read replicas for database queries
   - Redis cluster for distributed caching

## Cost Optimization

1. **Adzuna API**
   - Cache job data for 24 hours
   - Incremental updates instead of full fetch
   - Filter jobs by relevance before storing

2. **Google Cloud Talent Solution**
   - Use job expiry to auto-delete old jobs
   - Batch operations to reduce API calls
   - Cache search results for common queries

3. **Database**
   - Archive old jobs to cold storage
   - Compress job descriptions
   - Cleanup expired cache entries hourly

4. **Compute**
   - Auto-scale API instances based on load
   - Use spot/preemptible instances for workers
   - Optimize Docker images for faster startup

## Monitoring & Observability

- **Logging**: Structured logs with log levels (DEBUG, INFO, ERROR)
- **Metrics**: Track sync success/failure rates, API response times
- **Health Checks**: `/health` endpoint for load balancer probes
- **Database**: Monitor connection pool usage, slow queries
- **Alerts**: Set up alerts for sync failures, API errors

## Development

```bash
# Run tests
pytest

# Run with auto-reload
uvicorn app.main:app --reload

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Production Deployment

1. Set up PostgreSQL and Redis
2. Configure `.env` with production credentials
3. Run database migrations
4. Deploy with Docker Compose or Kubernetes
5. Set up load balancer and SSL
6. Configure monitoring and alerts
7. Test scheduled job refresh
8. Set up backup and disaster recovery

## Security Considerations

- Store credentials in `.env` (never commit)
- Use service account keys with minimal permissions
- Enable SSL/TLS for database connections
- Implement API rate limiting
- Add authentication/authorization for admin endpoints
- Regularly rotate API keys and credentials

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact the development team.
