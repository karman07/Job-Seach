#!/bin/bash

# Quick setup script for MongoDB version

echo "🚀 Job Matching API - MongoDB Setup"
echo "===================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  Please edit .env and add your credentials:"
    echo "   - ADZUNA_APP_ID"
    echo "   - ADZUNA_APP_KEY"
    echo "   - GCP_TENANT_ID"
    echo "   - CTS_COMPANY_NAME"
    echo ""
else
    echo "✓ .env file found"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create logs directory
mkdir -p logs
echo "✓ Logs directory created"

echo ""
echo "===================================="
echo "✅ Setup complete!"
echo ""
echo "To start the server:"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Or with Docker:"
echo "  docker-compose up --build"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo "===================================="
