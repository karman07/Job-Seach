# Job Matching Backend - MongoDB Version

Production-grade job matching backend using **MongoDB Atlas**, Adzuna API, and Google Cloud Talent Solution.

## 🎯 Key Features

- ✅ **MongoDB Atlas** cloud database (no local DB needed)
- ✅ **Automated daily job refresh** at configured time
- ✅ **AI-powered matching** via Google Cloud Talent Solution
- ✅ **Resume-to-job matching** with relevance scoring
- ✅ **Job description similarity** search
- ✅ **Flexible filtering** by salary, location, remote, internship
- ✅ **Production-ready** with error handling & logging

## 🏗️ Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: MongoDB Atlas (Cloud)
- **Matching Engine**: Google Cloud Talent Solution
- **Job Source**: Adzuna API
- **Scheduler**: APScheduler (built-in)

## 📁 Project Structure

```
job_arch/
├── app/
│   ├── api/                  # FastAPI endpoints
│   ├── services/             # Business logic (MongoDB async)
│   ├── integrations/         # Adzuna & CTS clients
│   ├── config.py            # Settings from .env
│   ├── database.py          # MongoDB connection
│   ├── models.py            # Pydantic models
│   ├── schemas.py           # API schemas
│   ├── scheduler.py         # APScheduler
│   └── main.py              # FastAPI app
├── youtube-data-api-v3-468414-e37ad1959b34.json  # Google credentials
├── .env.example             # Environment template
├── requirements.txt         # Dependencies
├── docker-compose.yml       # Docker setup
└── README_MONGODB.md        # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud project with Talent Solution API enabled
- Adzuna API credentials
- MongoDB Atlas account (connection string provided)

### 1. Clone and Setup

```bash
cd job_arch
chmod +x setup.sh
./setup.sh
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
# Adzuna API
ADZUNA_APP_ID=your_app_id_here
ADZUNA_APP_KEY=your_app_key_here

# Google Cloud
GCP_PROJECT_ID=youtube-data-api-v3-468414
GCP_TENANT_ID=your-tenant-id-here
CTS_COMPANY_NAME=projects/your-project/tenants/your-tenant/companies/your-company

# MongoDB (Already configured)
MONGODB_URL=mongodb+srv://karmanwork23_db_user:8813917626$k@cluster0.p5oiwsd.mongodb.net/?appName=Cluster0
MONGODB_DB_NAME=jobmatch_db

# Job Refresh Schedule
JOB_REFRESH_TIME=03:00
JOB_EXPIRY_DAYS=30
```

### 3. Run the Application

**Option A: Local Development**
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Option B: Docker**
```bash
docker-compose up --build
```

**Access the API:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## 📊 API Endpoints

### 1. Match Resume to Jobs
```bash
curl -X POST http://localhost:8000/match/resume \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Python developer with 5 years experience in FastAPI, MongoDB, and cloud services...",
    "location": "San Francisco",
    "job_level": "MID_LEVEL",
    "stipend_min": 100000
  }'
```

### 2. Find Similar Jobs by Description
```bash
curl -X POST http://localhost:8000/match/jd \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Looking for a backend developer proficient in Python...",
    "location": "Remote"
  }'
```

### 3. List Jobs with Filters
```bash
curl "http://localhost:8000/jobs?internship=true&remote=true&min_stipend=50000&limit=20"
```

### 4. Manual Job Refresh (Admin)
```bash
curl -X POST http://localhost:8000/admin/refresh-jobs
```

### 5. Health Check
```bash
curl http://localhost:8000/health
```

## 🗄️ MongoDB Collections

The system uses the following MongoDB collections:

1. **jobs** - Stores all job listings from Adzuna
2. **companies** - Company information for CTS
3. **job_sync_logs** - Tracks sync operations
4. **resume_search_cache** - Caches resume match results (24h TTL)

Indexes are automatically created on first connection for optimal performance.

## ⏰ Automated Job Refresh

The system automatically refreshes jobs daily at the time specified in `JOB_REFRESH_TIME` (default: 3:00 AM UTC).

**How it works:**
1. Fetches latest jobs from Adzuna (last 30 days)
2. Creates new jobs or updates existing ones
3. Syncs to Google Cloud Talent Solution
4. Marks expired jobs (older than `JOB_EXPIRY_DAYS`)
5. Logs the operation in `job_sync_logs` collection

**Manual trigger:**
```bash
curl -X POST http://localhost:8000/admin/refresh-jobs
```

## 🔧 Configuration

All configuration is in `.env`:

| Variable | Description | Example |
|----------|-------------|---------|
| `ADZUNA_APP_ID` | Adzuna API ID | `abc123` |
| `ADZUNA_APP_KEY` | Adzuna API Key | `xyz789` |
| `GCP_PROJECT_ID` | Google Cloud Project | `youtube-data-api-v3-468414` |
| `GCP_TENANT_ID` | CTS Tenant ID | Generated from CTS |
| `CTS_COMPANY_NAME` | Full company path | `projects/.../companies/...` |
| `MONGODB_URL` | MongoDB connection | Already configured |
| `MONGODB_DB_NAME` | Database name | `jobmatch_db` |
| `JOB_REFRESH_TIME` | Daily refresh time (HH:MM) | `03:00` |
| `JOB_EXPIRY_DAYS` | Job expiration days | `30` |

## 🧪 Testing

Test the API with the provided test script:

```bash
python test_api.py
```

Or use the interactive API docs:
```
http://localhost:8000/docs
```

## 📈 Monitoring

**View sync logs:**
```python
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def view_logs():
    client = AsyncIOMotorClient("your_mongodb_url")
    db = client.jobmatch_db
    
    logs = await db.job_sync_logs.find().sort("started_at", -1).limit(10).to_list(10)
    for log in logs:
        print(f"{log['sync_type']}: {log['status']} - Created: {log['jobs_created']}, Updated: {log['jobs_updated']}")

asyncio.run(view_logs())
```

**Check job count:**
```python
async def job_count():
    client = AsyncIOMotorClient("your_mongodb_url")
    db = client.jobmatch_db
    
    total = await db.jobs.count_documents({"status": "active"})
    internships = await db.jobs.count_documents({"status": "active", "is_internship": True})
    
    print(f"Total active jobs: {total}")
    print(f"Active internships: {internships}")

asyncio.run(job_count())
```

## 🐛 Troubleshooting

**MongoDB connection fails:**
- Check if the MongoDB URL is correct in `.env`
- Verify network access (MongoDB Atlas IP whitelist)
- Check if `dnspython` is installed: `pip install dnspython`

**CTS errors:**
- Verify `GOOGLE_APPLICATION_CREDENTIALS` points to the JSON file
- Ensure Talent Solution API is enabled in GCP
- Check if tenant/company IDs are correct

**No jobs found:**
- Trigger manual refresh: `curl -X POST http://localhost:8000/admin/refresh-jobs`
- Check Adzuna API credentials
- View sync logs in MongoDB

## 🚀 Deployment

**Google Cloud Run:**

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/jobmatch-api

# Deploy
gcloud run deploy jobmatch-api \
  --image gcr.io/PROJECT_ID/jobmatch-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="MONGODB_URL=..." \
  --memory 1Gi
```

**Heroku:**

```bash
heroku create jobmatch-api
heroku config:set MONGODB_URL="..."
heroku config:set ADZUNA_APP_ID="..."
git push heroku main
```

## 💰 Cost Estimate

- MongoDB Atlas (M0 Free Tier): $0
- Google Cloud Talent Solution: ~$0.75/1000 searches
- Adzuna API: Free (rate limited)
- Cloud Run (minimal): ~$5-10/month

**Total: ~$5-15/month**

## 📝 API Response Examples

**Resume Match Response:**
```json
{
  "total_matches": 15,
  "search_time_ms": 456.2,
  "jobs": [
    {
      "job_id": "507f1f77bcf86cd799439011",
      "title": "Senior Python Developer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "salary_min": 120000,
      "salary_max": 180000,
      "relevance_score": 0.95,
      "is_internship": false
    }
  ]
}
```

## 🔐 Security

- ✅ All credentials in `.env` (not committed)
- ✅ MongoDB Atlas with authentication
- ✅ Google service account with minimal permissions
- ✅ Input validation via Pydantic
- ✅ HTTPS required for production

## 📚 Documentation

- [API Examples](API_EXAMPLES.md)
- [Architecture](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)

## 🆘 Support

For issues or questions:
1. Check logs: `tail -f logs/app.log`
2. View MongoDB data: Use MongoDB Atlas UI
3. Test health: `curl http://localhost:8000/health`

## ✅ Ready to Use!

The system is now configured with:
- ✅ MongoDB Atlas cloud database
- ✅ Your Google service account JSON
- ✅ Production-ready architecture
- ✅ Automatic daily job refresh
- ✅ No local database installation needed

Just add your API credentials and start!
