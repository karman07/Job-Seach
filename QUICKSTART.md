# QUICKSTART - Job Matching Backend

## ⚡ 3-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Add API Keys to .env
Edit the `.env` file and add:
- **ADZUNA_APP_ID** - Get from https://developer.adzuna.com
- **ADZUNA_APP_KEY** - Get from https://developer.adzuna.com
- **GCP_TENANT_ID** - Get from Google Cloud Talent Solution console
- **CTS_COMPANY_NAME** - Create company in CTS first

### 3. Start Server
```bash
uvicorn app.main:app --reload
```

### 4. Test It
```bash
# Health check
curl http://localhost:8000/health

# Fetch jobs (triggers first sync)
curl -X POST http://localhost:8000/admin/refresh-jobs

# Test resume matching
python test_api.py
```

---

## 📊 What You Get

### ✅ Already Configured
- ✅ MongoDB Atlas connection (cloud database)
- ✅ Google service account (youtube-data-api-v3-468414-e37ad1959b34.json)
- ✅ Daily auto-refresh at 3:00 AM UTC
- ✅ All MongoDB indexes
- ✅ Error handling & logging

### 🔧 You Need to Add
- Adzuna API credentials (2 values)
- Google Cloud Talent Solution tenant ID
- Google Cloud Talent Solution company ID

---

## 🔑 Getting API Credentials

### Adzuna API (Free)
1. Go to https://developer.adzuna.com/signup
2. Sign up for free account
3. Copy `App ID` and `App Key`
4. Paste into `.env`

### Google Cloud Talent Solution
1. Go to https://console.cloud.google.com
2. Enable "Cloud Talent Solution API"
3. Create a tenant:
```bash
curl -X POST \
  https://jobs.googleapis.com/v4/projects/youtube-data-api-v3-468414/tenants \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{"externalId": "jobmatch-tenant"}'
```
4. Note the tenant ID from response
5. Create a company under that tenant
6. Note the full company name (projects/.../tenants/.../companies/...)
7. Add to `.env`

---

## 📋 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Check system status |
| POST | `/match/resume` | Match resume to jobs |
| POST | `/match/jd` | Find similar jobs |
| GET | `/jobs` | List jobs with filters |
| POST | `/admin/refresh-jobs` | Manual job sync |

**Full docs:** http://localhost:8000/docs

---

## 🐛 Common Issues

**"ADZUNA_APP_ID not set"**
→ Edit `.env` and add your Adzuna credentials

**"GCP_TENANT_ID not set"**
→ Create a tenant in Google Cloud Talent Solution

**"MongoServerError: bad auth"**
→ MongoDB password is already set correctly (contains special char `$`)

**"No jobs found"**
→ Run: `curl -X POST http://localhost:8000/admin/refresh-jobs`

---

## 🎯 Architecture (Simple)

```
┌─────────────┐
│  FastAPI    │  ← Your Backend
└──────┬──────┘
       │
       ├─► MongoDB Atlas (Cloud DB)
       ├─► Adzuna API (Job Source)
       └─► Google CTS (Matching AI)
```

**Total External Dependencies:** 3
- MongoDB Atlas (free tier)
- Adzuna API (free)
- Google Cloud Talent Solution (pay per use)

**No Redis, No PostgreSQL, No Celery needed!**

---

## ⏰ Auto-Refresh

Jobs refresh automatically every day at 3:00 AM UTC.

Change time in `.env`:
```env
JOB_REFRESH_TIME=03:00  # UTC time (HH:MM)
```

Jobs older than 30 days are marked as expired.

---

## 🚀 Deploy

**Docker (Recommended)**
```bash
docker-compose up -d
```

**Cloud Run**
```bash
gcloud run deploy jobmatch-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 📞 Need Help?

1. Check logs: `tail -f logs/app.log`
2. Test connection: `curl http://localhost:8000/health`
3. View MongoDB: https://cloud.mongodb.com (Atlas UI)
4. API playground: http://localhost:8000/docs

**Complete docs:** See [README_MONGODB.md](README_MONGODB.md)
