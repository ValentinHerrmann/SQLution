#!/bin/bash
# Stop development environment

echo "🛑 Stopping SQLution Development Environment..."
docker compose -f compose.dev.yaml down

echo "✅ Development environment stopped"
echo ""
echo "💡 To remove volumes as well, run:"
echo "   docker compose -f compose.dev.yaml down -v"
