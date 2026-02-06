# Docker Deployment - Ready to Deploy

## ✅ Files Prepared

All Docker deployment files are ready:

1. **Dockerfile** - Optimized production image with:
   - Python 3.11 slim base
   - Non-root user for security
   - Health checks
   - Minimal dependencies

2. **docker-compose.yml** - Development setup
3. **docker-compose.prod.yml** - Production setup with:
   - Resource limits (2 CPU, 2GB RAM)
   - Auto-restart policy
   - Log rotation
   - Health checks

4. **.dockerignore** - Excludes unnecessary files
5. **deploy.sh** - Automated deployment script
6. **DOCKER_DEPLOYMENT.md** - Complete deployment guide

## 🚀 Deployment Steps

### Prerequisites
1. Start Docker Desktop on your Mac
2. Ensure `.env` file is configured
3. Ensure Google credentials file exists

### Deploy

#### Option 1: Automated (Recommended)
```bash
./deploy.sh
```

#### Option 2: Manual
```bash
# Development
docker compose up --build

# Production
docker compose -f docker-compose.prod.yml up --build -d
```

#### Option 3: Direct Docker
```bash
# Build
docker build -t jobmatch-api:latest .

# Run
docker run -d \
  --name jobmatch_api \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/youtube-data-api-v3-468414-e37ad1959b34.json:/app/youtube-data-api-v3-468414-e37ad1959b34.json:ro \
  jobmatch-api:latest
```

## 📊 Verify Deployment

```bash
# Check if running
docker ps

# Check health
curl http://localhost:8000/health

# View logs
docker logs -f jobmatch_api

# API docs
open http://localhost:8000/docs
```

## 🔧 Management Commands

```bash
# Stop
docker stop jobmatch_api

# Start
docker start jobmatch_api

# Restart
docker restart jobmatch_api

# Remove
docker rm -f jobmatch_api

# Shell access
docker exec -it jobmatch_api /bin/bash
```

## 🌐 Cloud Deployment

### AWS ECS
```bash
# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag jobmatch-api:latest <account>.dkr.ecr.us-east-1.amazonaws.com/jobmatch-api:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/jobmatch-api:latest
```

### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/<project-id>/jobmatch-api
gcloud run deploy jobmatch-api \
  --image gcr.io/<project-id>/jobmatch-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### DigitalOcean App Platform
```bash
# Push to Docker Hub
docker tag jobmatch-api:latest username/jobmatch-api:latest
docker push username/jobmatch-api:latest
# Then deploy via DigitalOcean UI
```

## 📝 Next Steps

1. **Start Docker Desktop** if not running
2. **Run deployment**: `./deploy.sh`
3. **Test API**: `curl http://localhost:8000/health`
4. **Check docs**: http://localhost:8000/docs

## ⚠️ Current Status

Docker daemon is not running. Please:
1. Open Docker Desktop application
2. Wait for it to start
3. Run `./deploy.sh` or manual commands above

## 🔍 Troubleshooting

### Docker not running
```bash
# Check Docker status
docker info

# Start Docker Desktop from Applications
```

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Build fails
```bash
# Clean Docker cache
docker system prune -a

# Rebuild
docker build --no-cache -t jobmatch-api:latest .
```
