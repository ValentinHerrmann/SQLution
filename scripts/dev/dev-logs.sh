#!/bin/bash
# Watch logs from the development container

echo "📋 Watching development container logs..."
echo "Press Ctrl+C to stop"
echo ""
docker compose -f compose.dev.yaml logs -f
