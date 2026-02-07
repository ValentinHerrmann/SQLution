#!/bin/bash
# Quick development environment launcher

set -e

echo "🔄 Starting SQLution Development Environment..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from example..."
    cat > .env << 'EOL'
# Development Environment Variables
SECRET_KEY=dev-secret-key-change-in-production
DEBUG_MODE=True
DEVELOPMENT_MODE=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
SQLUTION_DB_DIR=/data

# Upload limits (100MB)
FILE_UPLOAD_MAX_MEMORY_SIZE=104857600
DATA_UPLOAD_MAX_MEMORY_SIZE=104857600

# Debugger (set to 1 to wait for debugger attachment)
WAIT_FOR_DEBUGGER=0

# SQL Query logging (set to DEBUG to see SQL queries)
SQL_DEBUG=INFO
EOL
    echo "✅ Created .env file with development defaults"
    echo ""
fi

# Build and start the dev container
echo "🏗️  Building development container..."
docker compose -f compose.dev.yaml build

echo ""
echo "🚀 Starting development container..."
docker compose -f compose.dev.yaml up -d

echo ""
echo "✅ Development environment is starting!"
echo ""
echo "📊 Viewing logs (Ctrl+C to stop viewing, container keeps running)..."
echo ""

# Follow logs
docker compose -f compose.dev.yaml logs -f
