#!/bin/bash
set -e

echo "Starting K9 Operations Management System..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h ${POSTGRES_HOST:-db} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-k9user}; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is ready!"

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Determine number of workers based on CPU cores
WORKERS=${GUNICORN_WORKERS:-$((2 * $(nproc) + 1))}
echo "Starting Gunicorn with $WORKERS workers..."

# Start Gunicorn
exec gunicorn app:app \
    --bind 0.0.0.0:5000 \
    --workers $WORKERS \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --access-logfile - \
    --error-logfile - \
    --log-level info