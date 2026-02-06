#!/bin/bash

set -e

echo "🚀 Job Matching API - Docker Deployment"
echo "========================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Check if Google credentials exist
if [ ! -f youtube-data-api-v3-468414-e37ad1959b34.json ]; then
    echo "⚠️  Warning: Google credentials file not found"
    echo "Make sure youtube-data-api-v3-468414-e37ad1959b34.json exists"
fi

# Create logs directory
mkdir -p logs

# Build and deploy
echo ""
echo "📦 Building Docker image..."
docker-compose -f docker-compose.prod.yml build

echo ""
echo "🔄 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo ""
echo "🏥 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Service is healthy!"
else
    echo "⚠️  Service health check failed. Checking logs..."
    docker-compose -f docker-compose.prod.yml logs --tail=50
fi

echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Useful commands:"
echo "  View logs:    docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop:         docker-compose -f docker-compose.prod.yml down"
echo "  Restart:      docker-compose -f docker-compose.prod.yml restart"
echo "  Shell access: docker exec -it jobmatch_api_prod /bin/bash"
echo ""
echo "🌐 API available at: http://localhost:8000"
echo "📖 API docs at: http://localhost:8000/docs"
