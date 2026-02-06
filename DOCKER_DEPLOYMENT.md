# Docker Deployment Guide

## Quick Start

### 1. Build and Deploy
```bash
./deploy.sh
```

### 2. Manual Deployment
```bash
# Development
docker-compose up --build

# Production
docker-compose -f docker-compose.prod.yml up --build -d
```

## Docker Commands

### Build
```bash
docker build -t jobmatch-api:latest .
```

### Run Container
```bash
docker run -d \
  --name jobmatch_api \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/youtube-data-api-v3-468414-e37ad1959b34.json:/app/youtube-data-api-v3-468414-e37ad1959b34.json:ro \
  jobmatch-api:latest
```

### View Logs
```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml logs -f

# Direct container
docker logs -f jobmatch_api_prod
```

### Stop Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### Restart Services
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Shell Access
```bash
docker exec -it jobmatch_api_prod /bin/bash
```

### Check Health
```bash
curl http://localhost:8000/health
```

## Environment Variables

Required in `.env`:
```env
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/?appName=Cluster0
MONGODB_DB_NAME=jobmatch_db
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
GCP_PROJECT_ID=your-project-id
GCP_TENANT_ID=your-tenant-id
CTS_COMPANY_NAME=projects/your-project/tenants/your-tenant/companies/your-company
GOOGLE_APPLICATION_CREDENTIALS=youtube-data-api-v3-468414-e37ad1959b34.json
```

## Production Deployment

### AWS ECS
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag jobmatch-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/jobmatch-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/jobmatch-api:latest
```

### Google Cloud Run
```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/<project-id>/jobmatch-api
gcloud run deploy jobmatch-api --image gcr.io/<project-id>/jobmatch-api --platform managed
```

### Docker Hub
```bash
docker tag jobmatch-api:latest username/jobmatch-api:latest
docker push username/jobmatch-api:latest
```

## Monitoring

### Resource Usage
```bash
docker stats jobmatch_api_prod
```

### Inspect Container
```bash
docker inspect jobmatch_api_prod
```

### Health Check
```bash
docker inspect --format='{{json .State.Health}}' jobmatch_api_prod | jq
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs jobmatch_api_prod

# Check if port is in use
lsof -i :8000
```

### MongoDB connection issues
```bash
# Test connection from container
docker exec -it jobmatch_api_prod python -c "from motor.motor_asyncio import AsyncIOMotorClient; print('OK')"
```

### Google credentials issues
```bash
# Verify file exists in container
docker exec -it jobmatch_api_prod ls -la youtube-data-api-v3-468414-e37ad1959b34.json
```

## Cleanup

### Remove containers
```bash
docker-compose -f docker-compose.prod.yml down -v
```

### Remove images
```bash
docker rmi jobmatch-api:latest
```

### Clean all
```bash
docker system prune -a --volumes
```
