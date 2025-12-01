#!/bin/bash
# Script to create a superuser in the running SQLution container

CONTAINER_NAME="${1:-sqlution-dev}"

echo "Creating superuser in container: $CONTAINER_NAME"
echo "You will be prompted for username, email, and password"
echo ""

docker exec -it "$CONTAINER_NAME" python manage.py createsuperuser
