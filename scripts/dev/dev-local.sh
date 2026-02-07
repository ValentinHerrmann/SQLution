#!/bin/bash
# Start Django development server with static file hot reload (local, no Docker)

set -e

cd "$(dirname "$0")/tutorial"

echo "🚀 Starting SQLution Development (Local Mode)"
echo ""

# Check if virtual environment exists
if [ ! -d "../.venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create it first:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source ../.venv/bin/activate

# Install/update dependencies
echo "📦 Checking dependencies..."
pip install -q watchdog 2>/dev/null || pip install watchdog

# Set environment variables
export DEBUG_MODE=True
export DEVELOPMENT_MODE=True
export DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1,0.0.0.0"
export SECRET_KEY="${SECRET_KEY:-dev-local-secret-key}"

# Run migrations
echo "🗄️  Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create admin user if needed
echo "✅ Checking for admin user..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', 'admin')
    print('Admin user created: admin/admin')
else:
    print('Admin user already exists')
EOF

echo ""
echo "🌟 Starting development server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "👤 Default admin credentials: admin/admin"
echo ""
echo "⚡ Hot reload enabled:"
echo "   - Python files: Auto-reload"
echo "   - Static files: Auto-collected"
echo "   - Templates: Auto-reload"
echo ""
echo "🛑 Press Ctrl+C to stop"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $WATCHER_PID 2>/dev/null
    exit 0
}

# Register cleanup function
trap cleanup SIGTERM SIGINT

# Start static file watcher in background
python watch_static.py &
WATCHER_PID=$!

# Start Django development server
python manage.py runserver 0.0.0.0:8000
