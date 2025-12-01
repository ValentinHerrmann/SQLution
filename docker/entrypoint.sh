#!/bin/sh
set -euo pipefail

cd /app/tutorial

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
