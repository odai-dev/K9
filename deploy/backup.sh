#!/bin/bash
# K9 Operations Management System - Backup Script
# Copy this file to /home/k9app/backup.sh and make it executable:
#   chmod +x /home/k9app/backup.sh
#
# Add to crontab for daily backups:
#   crontab -e
#   Add: 0 2 * * * /home/k9app/backup.sh >> /home/k9app/logs/backup.log 2>&1

# Configuration
BACKUP_DIR="/home/k9app/backups"
DB_NAME="k9_operations"
DB_USER="k9user"
DAYS_TO_KEEP=7
DATE=$(date +%Y%m%d_%H%M%S)

# Load environment variables
if [ -f /home/k9app/app/.env ]; then
    export $(cat /home/k9app/app/.env | grep -v '^#' | xargs)
fi

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

echo "=== Backup started at $(date) ==="

# Database backup
echo "Creating database backup..."
PGPASSWORD=$PGPASSWORD pg_dump -h localhost -U $DB_USER $DB_NAME > "$BACKUP_DIR/db_$DATE.sql"

if [ $? -eq 0 ]; then
    echo "Database backup successful"
    
    # Compress the backup
    gzip "$BACKUP_DIR/db_$DATE.sql"
    echo "Backup compressed: db_$DATE.sql.gz"
else
    echo "ERROR: Database backup failed!"
    exit 1
fi

# Backup uploads directory
echo "Creating uploads backup..."
if [ -d /home/k9app/app/uploads ]; then
    tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" -C /home/k9app/app uploads
    echo "Uploads backup successful: uploads_$DATE.tar.gz"
else
    echo "No uploads directory found, skipping..."
fi

# Delete old backups
echo "Cleaning old backups (keeping last $DAYS_TO_KEEP days)..."
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +$DAYS_TO_KEEP -delete
find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime +$DAYS_TO_KEEP -delete

# Show backup status
echo ""
echo "Current backups:"
ls -lh $BACKUP_DIR/
echo ""
echo "Total backup size: $(du -sh $BACKUP_DIR | cut -f1)"

echo "=== Backup completed at $(date) ==="
