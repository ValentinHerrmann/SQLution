#!/bin/bash
# Development startup script with hot reload support

set -e

echo "🚀 Starting SQLution Development Environment..."

# Wait for any dependencies if needed
sleep 2

# Navigate to Django project directory
cd /workspace/tutorial

echo "📦 Installing Python dependencies..."
pip install -q -r /workspace/requirements.txt

# Install development dependencies
echo "🔧 Installing development tools..."
pip install -q debugpy watchdog ipython django-debug-toolbar 2>/dev/null || true

echo "🗄️  Running database migrations..."
python manage.py migrate --noinput

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "✅ Creating superuser if needed..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', 'admin')
    print('Superuser created: admin/admin')
else:
    print('Superuser already exists')
EOF

echo ""
echo "🌟 Development server starting..."
echo "📍 Server will be available at: http://localhost:8000"
echo "🐛 Debug port available at: 5678"
echo "👤 Default admin credentials: admin/admin"
echo ""
echo "⚡ Hot reload is enabled - changes will be detected automatically!"
echo "   - Python files: Auto-reload on save"
echo "   - Static files: Auto-collected on save (via file watcher)"
echo "   - Templates: Auto-reload on save"
echo ""

# Start static file watcher in background
echo "👀 Starting static file watcher..."
python watch_static.py &
WATCHER_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $WATCHER_PID 2>/dev/null
    exit 0
}

# Register cleanup function
trap cleanup SIGTERM SIGINT

# Check if debugpy should wait for debugger (default: yes)
if [ "$WAIT_FOR_DEBUGGER" != "0" ]; then
    echo "🐛 Waiting for debugger to attach on port 5678..."
    python -m debugpy --listen 0.0.0.0:5678 --wait-for-client manage.py runserver 0.0.0.0:8000
else
    # Start Django development server with auto-reload
    python manage.py runserver 0.0.0.0:8000
fi
