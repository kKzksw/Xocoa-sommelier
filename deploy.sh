#!/bin/bash

# XOCOA V2 Deployment Script (Elite Architect Edition)
# Usage: ./deploy.sh

echo "🚀 [XOCOA] Starting V2 Production Deployment..."

# 1. Pull latest orchestration config
echo "📥 [XOCOA] Updating configuration..."
git pull origin main

# 2. Check for .env file
if [ ! -f .env ]; then
    echo "❌ [ERROR] .env file not found! Please create it."
    exit 1
fi

# 3. Pull latest pre-built images from GitHub Registry
echo "⬇️  [XOCOA] Pulling latest containers from GHCR..."
docker-compose -f docker-compose.v2.yml pull

# 4. Restart services
echo "🔄 [XOCOA] Restarting services on V2 Infrastructure..."
docker-compose -f docker-compose.v2.yml up -d --remove-orphans

# 5. Database Maintenance
echo "🗄️  [XOCOA] Running Database Migrations..."
# Ensure the backend container is up
sleep 5
docker exec xocoa_backend python tools/migrate_to_postgres.py

# 6. Cleanup
echo "🧹 [XOCOA] Pruning old images..."
docker image prune -f

echo "✅ [XOCOA] V2 Deployment Complete! System is live."
echo "📊 Monitoring: https://xocoa.co/grafana (if configured) or <ip>:3001"
