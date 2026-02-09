#!/bin/bash

# XOCOA Production Deployment Script
# Usage: ./deploy.sh

echo "🚀 [XOCOA] Starting Deployment..."

# 1. Pull latest code (assuming this runs in the git repo)
echo "📥 [XOCOA] Pulling latest code..."
git pull origin main

# 2. Check for .env file
if [ ! -f .env ]; then
    echo "❌ [ERROR] .env file not found! Please create it with GROQ_API_KEY."
    exit 1
fi

# 3. Build and Deploy
echo "🏗️  [XOCOA] Building and Starting Containers..."
docker-compose -f docker-compose.prod.yml up --build -d

# 4. Cleanup
echo "🧹 [XOCOA] Cleaning up old images..."
docker image prune -f

echo "✅ [XOCOA] Deployment Complete! System is live."
