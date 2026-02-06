# Deploy to Google Cloud VM Instance - Step by Step

## Part 1: Create VM Instance

### Step 1: Create VM via Google Cloud Console
```bash
# Or use gcloud CLI
gcloud compute instances create jobmatch-api-vm \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-standard \
  --tags=http-server,https-server \
  --metadata=startup-script='#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose git
systemctl start docker
systemctl enable docker
usermod -aG docker $USER'
```

### Step 2: Configure Firewall
```bash
# Allow HTTP traffic
gcloud compute firewall-rules create allow-http-8000 \
  --project=youtube-data-api-v3-468414 \
  --allow=tcp:8000 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server
```

## Part 2: Setup VM

### Step 3: SSH into VM
```bash
gcloud compute ssh jobmatch-api-vm \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a
```

### Step 4: Install Docker (if not done via startup script)
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y docker.io docker-compose git

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again for group changes
exit
# SSH back in
```

### Step 5: Install Docker Compose V2
```bash
sudo apt-get install -y docker-compose-plugin
```

## Part 3: Deploy Application

### Step 6: Clone/Upload Project
```bash
# Option A: Clone from Git (if you have a repo)
git clone <your-repo-url> jobmatch-api
cd jobmatch-api

# Option B: Upload from local machine
# On your local machine:
gcloud compute scp --recurse \
  /Users/karmansingh/Desktop/work/ai_interview/job_arch \
  jobmatch-api-vm:~/jobmatch-api \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a
```

### Step 7: Create .env file on VM
```bash
cd ~/jobmatch-api

# Create .env file
cat > .env << 'EOF'
# MongoDB Configuration
MONGODB_URL=mongodb+srv://karmanwork23_db_user:8813917626$k@cluster0.p5oiwsd.mongodb.net/?appName=Cluster0
MONGODB_DB_NAME=jobmatch_db

# Adzuna API
ADZUNA_APP_ID=your_adzuna_app_id_here
ADZUNA_APP_KEY=your_adzuna_app_key_here

# Google Cloud Configuration
GCP_PROJECT_ID=youtube-data-api-v3-468414
GOOGLE_APPLICATION_CREDENTIALS=youtube-data-api-v3-468414-e37ad1959b34.json

# Google Cloud Talent Solution
GCP_TENANT_ID=prod
CTS_COMPANY_NAME=projects/youtube-data-api-v3-468414/tenants/YOUR_TENANT_ID/companies/YOUR_COMPANY_ID

# Job Refresh Configuration
JOB_REFRESH_TIME=03:00
JOB_EXPIRY_DAYS=30

# Application Settings
LOG_LEVEL=INFO
EOF
```

### Step 8: Upload Google Credentials
```bash
# On your local machine:
gcloud compute scp \
  /Users/karmansingh/Desktop/work/ai_interview/job_arch/youtube-data-api-v3-468414-e37ad1959b34.json \
  jobmatch-api-vm:~/jobmatch-api/ \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a
```

### Step 9: Build and Run
```bash
# On VM
cd ~/jobmatch-api

# Create logs directory
mkdir -p logs

# Build Docker image
docker build -t jobmatch-api:latest .

# Run container
docker run -d \
  --name jobmatch_api \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/youtube-data-api-v3-468414-e37ad1959b34.json:/app/youtube-data-api-v3-468414-e37ad1959b34.json:ro \
  jobmatch-api:latest
```

### Step 10: Verify Deployment
```bash
# Check if container is running
docker ps

# Check logs
docker logs -f jobmatch_api

# Test health endpoint
curl http://localhost:8000/health

# Test from outside (use VM external IP)
curl http://<VM_EXTERNAL_IP>:8000/health
```

## Part 4: Get VM External IP

### Step 11: Find External IP
```bash
# On local machine
gcloud compute instances describe jobmatch-api-vm \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# Or in VM
curl ifconfig.me
```

### Step 12: Access API
```
API URL: http://<EXTERNAL_IP>:8000
API Docs: http://<EXTERNAL_IP>:8000/docs
Health: http://<EXTERNAL_IP>:8000/health
```

## Part 5: Management Commands

### View Logs
```bash
docker logs -f jobmatch_api
```

### Restart Application
```bash
docker restart jobmatch_api
```

### Stop Application
```bash
docker stop jobmatch_api
```

### Update Application
```bash
# Pull latest code
git pull  # or upload new files

# Rebuild
docker build -t jobmatch-api:latest .

# Stop old container
docker stop jobmatch_api
docker rm jobmatch_api

# Start new container
docker run -d \
  --name jobmatch_api \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/youtube-data-api-v3-468414-e37ad1959b34.json:/app/youtube-data-api-v3-468414-e37ad1959b34.json:ro \
  jobmatch-api:latest
```

### Shell Access
```bash
docker exec -it jobmatch_api /bin/bash
```

## Part 6: Optional - Setup with Docker Compose

### Alternative: Use Docker Compose
```bash
# On VM
cd ~/jobmatch-api

# Run with docker compose
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Stop
docker compose -f docker-compose.prod.yml down
```

## Part 7: Setup SSL (Optional but Recommended)

### Install Nginx and Certbot
```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Configure Nginx
sudo nano /etc/nginx/sites-available/jobmatch-api

# Add this configuration:
server {
    listen 80;
    server_name <your-domain.com>;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/jobmatch-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d <your-domain.com>
```

## Part 8: Monitoring

### Setup Log Rotation
```bash
# Create logrotate config
sudo nano /etc/logrotate.d/jobmatch-api

# Add:
/home/$USER/jobmatch-api/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### Monitor Resources
```bash
# CPU and Memory
docker stats jobmatch_api

# Disk usage
df -h

# Docker disk usage
docker system df
```

## Quick Reference Commands

```bash
# SSH to VM
gcloud compute ssh jobmatch-api-vm --project=youtube-data-api-v3-468414 --zone=us-central1-a

# Upload files
gcloud compute scp --recurse ./local-folder jobmatch-api-vm:~/remote-folder --project=youtube-data-api-v3-468414 --zone=us-central1-a

# Check container status
docker ps -a

# View logs
docker logs -f jobmatch_api

# Restart
docker restart jobmatch_api

# Get external IP
gcloud compute instances describe jobmatch-api-vm --project=youtube-data-api-v3-468414 --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

## Troubleshooting

### Container won't start
```bash
docker logs jobmatch_api
docker inspect jobmatch_api
```

### Port not accessible
```bash
# Check firewall
gcloud compute firewall-rules list --project=youtube-data-api-v3-468414

# Check if port is listening
sudo netstat -tlnp | grep 8000
```

### Out of disk space
```bash
# Clean Docker
docker system prune -a

# Clean logs
sudo find /var/log -type f -name "*.log" -delete
```

### MongoDB connection issues
```bash
# Test from container
docker exec -it jobmatch_api python -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; asyncio.run(AsyncIOMotorClient('YOUR_MONGODB_URL').admin.command('ping')); print('Connected!')"
```
