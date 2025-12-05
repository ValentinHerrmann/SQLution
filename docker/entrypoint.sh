#!/bin/sh
set -euo pipefail

cd /app/tutorial

python manage.py collectstatic --noinput
python manage.py makemigrations --noinput
python manage.py migrate --noinput

exec "$@"
