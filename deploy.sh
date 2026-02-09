#!/bin/bash

# XOCOA Professional Deployment Script
# Usage: ./deploy.sh

echo "🚀 [XOCOA] Starting Zero-Downtime Deployment..."

# 1. Pull latest orchestration config (docker-compose files)
echo "📥 [XOCOA] Updating configuration..."
git pull origin main

# 2. Check for .env file
if [ ! -f .env ]; then
    echo "❌ [ERROR] .env file not found! Please create it."
    exit 1
fi

# 3. Pull latest pre-built images from GitHub Registry
echo "⬇️  [XOCOA] Pulling latest containers from GHCR..."
docker-compose -f docker-compose.prod.yml pull

# 4. Restart services (Zero-Downtime rolling update logic handled by Compose)
echo "🔄 [XOCOA] Restarting services..."
docker-compose -f docker-compose.prod.yml up -d

# 5. Cleanup
echo "🧹 [XOCOA] Pruning old images..."
docker image prune -f

echo "✅ [XOCOA] Deployment Complete! System is live with latest code."