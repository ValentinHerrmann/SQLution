#!/bin/bash
# Execute Django management commands in the dev container

if [ $# -eq 0 ]; then
    echo "Usage: ./dev-manage.sh <command> [args...]"
    echo ""
    echo "Examples:"
    echo "  ./dev-manage.sh migrate"
    echo "  ./dev-manage.sh makemigrations"
    echo "  ./dev-manage.sh createsuperuser"
    echo "  ./dev-manage.sh shell"
    echo "  ./dev-manage.sh collectstatic"
    echo "  ./dev-manage.sh test"
    exit 1
fi

docker compose -f compose.dev.yaml exec sqlution-dev python manage.py "$@"
