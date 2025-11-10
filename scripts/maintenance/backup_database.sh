#!/bin/bash
set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ibco_backup_$TIMESTAMP.sql.gz"

echo "Creating database backup..."

mkdir -p $BACKUP_DIR

# Create backup
docker compose -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U $DATABASE_USER $DATABASE_NAME | gzip > $BACKUP_FILE

echo "✅ Backup created: $BACKUP_FILE"

# Keep only last 30 days of backups
find $BACKUP_DIR -name "ibco_backup_*.sql.gz" -mtime +30 -delete

echo "✅ Old backups cleaned up (kept last 30 days)"

# Show backup size
size=$(du -h "$BACKUP_FILE" | cut -f1)
echo "📦 Backup size: $size"
