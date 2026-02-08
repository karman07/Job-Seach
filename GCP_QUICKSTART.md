# GCP VM Deployment - Quick Start Checklist

## ✅ Pre-Deployment Checklist

- [ ] Google Cloud SDK installed (`gcloud --version`)
- [ ] Authenticated with GCP (`gcloud auth login`)
- [ ] Project set (`gcloud config set project youtube-data-api-v3-468414`)
- [ ] `.env` file configured with all credentials
- [ ] Google credentials JSON file present
- [ ] Billing enabled on GCP project

## 🚀 Deployment Options

### Option 1: Automated (Easiest)
```bash
./deploy_gcp_vm.sh
```

### Option 2: Manual Step-by-Step

#### 1. Create VM
```bash
gcloud compute instances create jobmatch-api-vm \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --tags=http-server,https-server
```

#### 2. Configure Firewall
```bash
gcloud compute firewall-rules create allow-http-8000 \
  --project=youtube-data-api-v3-468414 \
  --allow=tcp:8000 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server
```

#### 3. Upload Files
```bash
gcloud compute scp --recurse \
  /Users/karmansingh/Desktop/work/ai_interview/job_arch \
  jobmatch-api-vm:~/jobmatch-api \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a
```

#### 4. SSH to VM
```bash
gcloud compute ssh jobmatch-api-vm \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a
```

#### 5. Install Docker (on VM)
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
exit  # logout and login again
```

#### 6. Deploy (on VM after re-login)
```bash
cd ~/jobmatch-api
mkdir -p logs

docker build -t jobmatch-api:latest .

docker run -d \
  --name jobmatch_api \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/youtube-data-api-v3-468414-e37ad1959b34.json:/app/youtube-data-api-v3-468414-e37ad1959b34.json:ro \
  jobmatch-api:latest
```

#### 7. Get External IP
```bash
gcloud compute instances describe jobmatch-api-vm \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

#### 8. Test
```bash
curl http://<EXTERNAL_IP>:8000/health
```

## 📊 Post-Deployment

### Access API
- API: `http://<EXTERNAL_IP>:8000`
- Docs: `http://<EXTERNAL_IP>:8000/docs`
- Health: `http://<EXTERNAL_IP>:8000/health`

### View Logs
```bash
gcloud compute ssh jobmatch-api-vm \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a \
  --command='docker logs -f jobmatch_api'
```

### Update Application
```bash
# Upload new files
gcloud compute scp --recurse \
  /Users/karmansingh/Desktop/work/ai_interview/job_arch \
  jobmatch-api-vm:~/jobmatch-api \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a

# SSH and rebuild
gcloud compute ssh jobmatch-api-vm \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a \
  --command='cd ~/jobmatch-api && \
    docker build -t jobmatch-api:latest . && \
    docker stop jobmatch_api && \
    docker rm jobmatch_api && \
    docker run -d --name jobmatch_api --restart unless-stopped -p 8000:8000 --env-file .env -v $(pwd)/logs:/app/logs -v $(pwd)/youtube-data-api-v3-468414-e37ad1959b34.json:/app/youtube-data-api-v3-468414-e37ad1959b34.json:ro jobmatch-api:latest'
```

## 🛠️ Management

### Stop VM (save costs)
```bash
gcloud compute instances stop jobmatch-api-vm \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a
```

### Start VM
```bash
gcloud compute instances start jobmatch-api-vm \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a
```

### Delete VM
```bash
gcloud compute instances delete jobmatch-api-vm \
  --project=youtube-data-api-v3-468414 \
  --zone=us-central1-a
```

## 💰 Cost Estimate

- **e2-medium VM**: ~$24/month (730 hours)
- **20GB Standard Disk**: ~$0.80/month
- **Network Egress**: ~$0.12/GB
- **Total**: ~$25-30/month

### Save Costs
- Stop VM when not in use
- Use preemptible instances (60-90% cheaper)
- Use smaller machine type (e2-small)

## 🔒 Security Best Practices

1. **Restrict firewall**: Change `0.0.0.0/0` to specific IPs
2. **Setup SSL**: Use Nginx + Let's Encrypt
3. **Use secrets manager**: Store credentials in GCP Secret Manager
4. **Enable monitoring**: Setup Cloud Monitoring alerts
5. **Regular updates**: Keep system and Docker updated

## 📝 Next Steps

1. Run `./deploy_gcp_vm.sh`
2. Wait for deployment to complete
3. Test API at `http://<EXTERNAL_IP>:8000/health`
4. Configure domain name (optional)
5. Setup SSL certificate (recommended)
6. Configure monitoring and alerts
