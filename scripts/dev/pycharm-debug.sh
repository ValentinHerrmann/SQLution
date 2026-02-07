#!/bin/bash
# PyCharm Debug Helper - Ensures container is ready for debugging

set -e

echo "🐍 PyCharm Debug Setup"
echo "====================="
echo ""

# Check if container is running
if ! docker ps | grep -q sqlution-dev; then
    echo "📦 Container not running. Starting..."
    ./dev-start.sh &
    CONTAINER_STARTED=1

    # Wait for container to be ready
    echo "⏳ Waiting for container to start..."
    sleep 5

    # Wait for Django to be ready
    echo "⏳ Waiting for Django server..."
    for i in {1..30}; do
        if docker logs sqlution-dev 2>&1 | grep -q "Waiting for debugger"; then
            echo "✅ Django is waiting for debugger"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ Timeout waiting for Django"
            exit 1
        fi
        sleep 1
    done
else
    echo "✅ Container is already running"

    # Check if Django is waiting for debugger
    if docker logs sqlution-dev 2>&1 | tail -20 | grep -q "Waiting for debugger"; then
        echo "✅ Django is waiting for debugger"
    else
        echo "⚠️  Django may not be waiting for debugger"
        echo "   Current status:"
        docker logs sqlution-dev 2>&1 | tail -5
    fi
fi

echo ""
echo "🔧 Setup Complete!"
echo ""
echo "Next steps in PyCharm:"
echo "1. Go to Run → Attach to Process (or press Ctrl+Alt+F5)"
echo "2. Look for process on 'localhost:5678'"
echo "3. Click to attach the debugger"
echo "4. Set breakpoints and start debugging!"
echo ""
echo "Alternative (without debugging):"
echo "• Select 'Django in Container (Run)' → Run (Shift+F10)"
echo ""
echo "📍 Server URL: http://localhost:8000"
echo "🐛 Debug Port: 5678"
echo ""
