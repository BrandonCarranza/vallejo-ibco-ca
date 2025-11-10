#!/bin/bash
set -e

echo "=== IBCo Production Deployment ==="
echo ""

# Check environment
if [ "$ENVIRONMENT" != "production" ]; then
    echo "❌ ENVIRONMENT must be set to 'production'"
    exit 1
fi

# Check required environment variables
required_vars=("DATABASE_NAME" "DATABASE_USER" "DATABASE_PASSWORD" "REDIS_PASSWORD" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable not set: $var"
        exit 1
    fi
done

echo "✅ Environment variables validated"
echo ""

# Backup database before deployment
echo "📦 Creating database backup..."
./scripts/maintenance/backup_database.sh

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Build Docker images
echo "🔨 Building Docker images..."
docker compose -f docker-compose.prod.yml build

# Stop old containers
echo "🛑 Stopping old containers..."
docker compose -f docker-compose.prod.yml down

# Run database migrations
echo "🔄 Running database migrations..."
docker compose -f docker-compose.prod.yml run --rm api \
    poetry run alembic upgrade head

# Start new containers
echo "🚀 Starting new containers..."
docker compose -f docker-compose.prod.yml up -d

# Wait for health checks
echo "⏳ Waiting for health checks..."
sleep 10

# Smoke test
echo "🧪 Running smoke tests..."
./scripts/deploy/smoke-test.sh

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "Services:"
echo "- API: https://ibco-ca.us/api"
echo "- Docs: https://ibco-ca.us/docs"
echo "- Dashboard: https://ibco-ca.us/dashboard"
