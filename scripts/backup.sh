#!/bin/bash
# Database backup script for K9 Operations Management System

set -e

# Configuration
DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-k9operations}"
DB_USER="${POSTGRES_USER:-k9user}"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/k9_backup_$DATE.sql"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

echo "Starting database backup: $DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create database backup
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --no-password \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=custom \
    --file="$BACKUP_FILE.custom"

# Also create plain SQL backup for easier inspection
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --no-password \
    --clean \
    --if-exists \
    --create \
    --format=plain \
    --file="$BACKUP_FILE"

# Compress the plain SQL backup
gzip "$BACKUP_FILE"

echo "Database backup completed: $BACKUP_FILE.gz"
echo "Custom format backup: $BACKUP_FILE.custom"

# Clean up old backups
if [ "$RETENTION_DAYS" -gt 0 ]; then
    echo "Cleaning up backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "k9_backup_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete
    find "$BACKUP_DIR" -name "k9_backup_*.custom" -mtime +"$RETENTION_DAYS" -delete
    echo "Cleanup completed"
fi

# Log backup info
echo "Backup summary:" >> "$BACKUP_DIR/backup.log"
echo "Date: $DATE" >> "$BACKUP_DIR/backup.log"
echo "File: $(basename "$BACKUP_FILE.gz")" >> "$BACKUP_DIR/backup.log"
echo "Size: $(du -h "$BACKUP_FILE.gz" | cut -f1)" >> "$BACKUP_DIR/backup.log"
echo "---" >> "$BACKUP_DIR/backup.log"

echo "Backup completed successfully!"