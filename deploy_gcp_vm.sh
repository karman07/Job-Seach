#!/bin/bash

# GCP VM Deployment Script
# Run this on your LOCAL machine

set -e

PROJECT_ID="youtube-data-api-v3-468414"
ZONE="us-central1-a"
VM_NAME="jobmatch-api-vm"
MACHINE_TYPE="e2-medium"

echo "🚀 Google Cloud VM Deployment for Job Matching API"
echo "=================================================="

# Step 1: Create VM
echo ""
echo "📦 Step 1: Creating VM instance..."
gcloud compute instances create $VM_NAME \
  --project=$PROJECT_ID \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-standard \
  --tags=http-server,https-server \
  --metadata=startup-script='#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose-plugin git
systemctl start docker
systemctl enable docker
usermod -aG docker $(whoami)' || echo "VM already exists"

# Step 2: Configure Firewall
echo ""
echo "🔥 Step 2: Configuring firewall..."
gcloud compute firewall-rules create allow-http-8000 \
  --project=$PROJECT_ID \
  --allow=tcp:8000 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server || echo "Firewall rule already exists"

# Step 3: Wait for VM to be ready
echo ""
echo "⏳ Step 3: Waiting for VM to be ready..."
sleep 30

# Step 4: Upload project files
echo ""
echo "📤 Step 4: Uploading project files..."
gcloud compute scp --recurse \
  --project=$PROJECT_ID \
  --zone=$ZONE \
  $(pwd) $VM_NAME:~/jobmatch-api

# Step 5: Setup and deploy
echo ""
echo "🔧 Step 5: Setting up application on VM..."
gcloud compute ssh $VM_NAME \
  --project=$PROJECT_ID \
  --zone=$ZONE \
  --command="cd ~/jobmatch-api && \
    mkdir -p logs && \
    docker build -t jobmatch-api:latest . && \
    docker stop jobmatch_api 2>/dev/null || true && \
    docker rm jobmatch_api 2>/dev/null || true && \
    docker run -d \
      --name jobmatch_api \
      --restart unless-stopped \
      -p 8000:8000 \
      --env-file .env \
      -v \$(pwd)/logs:/app/logs \
      -v \$(pwd)/youtube-data-api-v3-468414-e37ad1959b34.json:/app/youtube-data-api-v3-468414-e37ad1959b34.json:ro \
      jobmatch-api:latest"

# Step 6: Get external IP
echo ""
echo "🌐 Step 6: Getting external IP..."
EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME \
  --project=$PROJECT_ID \
  --zone=$ZONE \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "📊 VM Details:"
echo "  Name: $VM_NAME"
echo "  Zone: $ZONE"
echo "  External IP: $EXTERNAL_IP"
echo ""
echo "🌐 Access your API:"
echo "  API URL: http://$EXTERNAL_IP:8000"
echo "  API Docs: http://$EXTERNAL_IP:8000/docs"
echo "  Health Check: http://$EXTERNAL_IP:8000/health"
echo ""
echo "📝 Useful commands:"
echo "  SSH to VM: gcloud compute ssh $VM_NAME --project=$PROJECT_ID --zone=$ZONE"
echo "  View logs: gcloud compute ssh $VM_NAME --project=$PROJECT_ID --zone=$ZONE --command='docker logs -f jobmatch_api'"
echo "  Stop VM: gcloud compute instances stop $VM_NAME --project=$PROJECT_ID --zone=$ZONE"
echo "  Delete VM: gcloud compute instances delete $VM_NAME --project=$PROJECT_ID --zone=$ZONE"
