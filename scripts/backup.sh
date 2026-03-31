#!/bin/bash
set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "📦 Starting database backup..."

# Создаем директорию для бэкапов
mkdir -p ${BACKUP_DIR}

# Бэкап базы данных
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} | gzip > ${BACKUP_DIR}/backup_${DATE}.sql.gz

# Удаляем старые бэкапы (старше 30 дней)
find ${BACKUP_DIR} -name "backup_*.sql.gz" -mtime +30 -delete

echo "✅ Backup completed: backup_${DATE}.sql.gz"