# Production deployment on Google Cloud Platform

## Prerequisites
- Google Cloud account with billing enabled
- gcloud CLI installed
- Docker installed

## Services to Set Up

### 1. Cloud SQL (PostgreSQL)
```bash
# Create PostgreSQL instance
gcloud sql instances create jobmatch-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create jobmatch_db --instance=jobmatch-db

# Create user
gcloud sql users create jobmatch \
  --instance=jobmatch-db \
  --password=SECURE_PASSWORD
```

### 2. Cloud Memorystore (Redis)
```bash
# Create Redis instance
gcloud redis instances create jobmatch-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0
```

### 3. Cloud Run (API)
```bash
# Build and push Docker image
gcloud builds submit --tag gcr.io/PROJECT_ID/jobmatch-api

# Deploy to Cloud Run
gcloud run deploy jobmatch-api \
  --image gcr.io/PROJECT_ID/jobmatch-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="DATABASE_URL=postgresql://..." \
  --set-env-vars="REDIS_URL=redis://..." \
  --memory 1Gi \
  --cpu 2 \
  --max-instances 10
```

### 4. Cloud Scheduler (Daily Job Refresh)
```bash
# Create scheduler job
gcloud scheduler jobs create http daily-job-refresh \
  --schedule="0 3 * * *" \
  --uri="https://your-api-url/admin/refresh-jobs" \
  --http-method=POST \
  --time-zone="UTC"
```

## Cost Estimates (Monthly)

- Cloud SQL (db-f1-micro): ~$15
- Cloud Memorystore (1GB): ~$35
- Cloud Run (avg usage): ~$20-50
- Cloud Talent Solution API: $0.75 per 1000 searches
- Adzuna API: Free (rate limited)

**Total: ~$70-100/month for moderate usage**

## Scaling Configuration

### For 5k jobs/day:
- Cloud SQL: db-f1-micro (1 vCPU, 1.7GB RAM)
- Cloud Run: 1-2 instances, 1GB memory
- Redis: 1GB

### For 50k jobs/day:
- Cloud SQL: db-n1-standard-1 (1 vCPU, 3.75GB RAM)
- Cloud Run: 5-10 instances, 2GB memory each
- Redis: 5GB
- Consider Cloud Tasks for job queue

## Security Checklist

- [ ] Use Secret Manager for credentials
- [ ] Enable Cloud SQL SSL connections
- [ ] Configure VPC for private networking
- [ ] Set up Cloud Armor for DDoS protection
- [ ] Enable Cloud Logging and Monitoring
- [ ] Configure IAM roles with least privilege
- [ ] Set up automated backups for Cloud SQL
- [ ] Use Cloud KMS for encryption keys
