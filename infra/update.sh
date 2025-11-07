#!/usr/bin/env bash
set -e

##############################################
# Floor Plan Analyzer - Update Script
# للتحديث بدون إيقاف الخدمة
##############################################

PROJECT_NAME="floor-plan-analyzer"
DEPLOY_DIR="/opt/${PROJECT_NAME}"

echo "🔄 Updating Floor Plan Analyzer..."

cd ${DEPLOY_DIR}

# Pull latest changes (if using git)
if [ -d ".git" ]; then
    git pull
fi

# Rebuild containers
docker-compose build

# Rolling update
docker-compose up -d --no-deps --build api

echo "✅ Update completed!"
docker-compose ps
