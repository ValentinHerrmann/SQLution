#!/bin/bash
# Open a bash shell in the development container

echo "🐚 Opening shell in development container..."
docker compose -f compose.dev.yaml exec sqlution-dev bash
