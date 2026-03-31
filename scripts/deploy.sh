#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Проверка переменных окружения
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Загрузка переменных
source .env

# Бэкап базы данных
echo "📦 Backing up database..."
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup_$(date +%Y%m%d_%H%M%S).sql

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Build and restart
echo "🏗️ Building containers..."
docker-compose -f docker-compose.prod.yml build

echo "🔄 Restarting services..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.prod.yml exec app python init_db.py init

# Clean old images
echo "🧹 Cleaning old images..."
docker image prune -f

echo "✅ Deployment completed!"
docker-compose -f docker-compose.prod.yml ps