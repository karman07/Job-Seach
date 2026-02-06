#!/bin/bash

# Production deployment script for Job Matching API

set -e

echo "🚀 Starting Job Matching API Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

echo -e "${GREEN}✓${NC} Environment file found"

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $python_version"

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -r requirements.txt

# Run database migrations
echo -e "${YELLOW}🗄️  Running database migrations...${NC}"
alembic upgrade head

# Create logs directory
mkdir -p logs

echo -e "${GREEN}✓${NC} Database migrations complete"

# Ask user which mode to run
echo ""
echo "Select deployment mode:"
echo "1) Development (single process with APScheduler)"
echo "2) Production (with Celery workers)"
echo "3) Docker Compose (all services)"
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo -e "${YELLOW}🔧 Starting in Development mode...${NC}"
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    2)
        echo -e "${YELLOW}🔧 Starting in Production mode with Celery...${NC}"
        echo "Starting API server, Celery worker, and Celery beat"
        echo "Make sure Redis is running!"
        
        # Start Celery worker in background
        celery -A app.tasks.celery_app worker --loglevel=info --detach
        
        # Start Celery beat in background
        celery -A app.tasks.celery_app beat --loglevel=info --detach
        
        # Start API server in foreground
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
        ;;
    3)
        echo -e "${YELLOW}🐳 Starting with Docker Compose...${NC}"
        docker-compose up --build
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}✓ Deployment complete!${NC}"
