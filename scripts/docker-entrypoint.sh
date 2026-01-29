#!/bin/bash
# docker-entrypoint.sh
# FlyReady Lab - Container Entrypoint Script

set -e

echo "==================================="
echo "FlyReady Lab - Starting Application"
echo "==================================="

# Wait for database
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database..."
    while ! pg_isready -h postgres -p 5432 -U ${POSTGRES_USER:-flyready} -q; do
        echo "Database is not ready - sleeping"
        sleep 2
    done
    echo "Database is ready!"
fi

# Wait for Redis
if [ -n "$REDIS_URL" ]; then
    echo "Waiting for Redis..."
    while ! redis-cli -h redis ping > /dev/null 2>&1; do
        echo "Redis is not ready - sleeping"
        sleep 2
    done
    echo "Redis is ready!"
fi

# Run database migrations
if [ -f "alembic.ini" ]; then
    echo "Running database migrations..."
    alembic upgrade head || echo "Migration failed or already up to date"
fi

# Create necessary directories
mkdir -p logs data metrics

# Set permissions
chown -R appuser:appgroup logs data metrics 2>/dev/null || true

echo "Starting application..."
exec "$@"
