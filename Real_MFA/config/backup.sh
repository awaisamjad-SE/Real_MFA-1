#!/bin/bash
# Real_MFA Backup Script
# Run daily via cron: 0 2 * * * /home/realuser/real_mfa/config/backup.sh
# Backs up PostgreSQL database and important directories

BACKUP_DIR="/home/realuser/backups"
DB_NAME="real_mfa_db"
DB_USER="real_mfa_user"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/real_mfa_db_${TIMESTAMP}.sql.gz"

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

# PostgreSQL backup
echo "Backing up database..."
sudo -u postgres pg_dump ${DB_NAME} | gzip > ${BACKUP_FILE}

# Keep only last 7 days of backups
find ${BACKUP_DIR} -name "real_mfa_db_*.sql.gz" -mtime +7 -delete

# Optional: Upload to S3 (requires AWS CLI)
# aws s3 cp ${BACKUP_FILE} s3://your-bucket/backups/

echo "Backup completed: ${BACKUP_FILE}"

# Log backup size
ls -lh ${BACKUP_FILE}
