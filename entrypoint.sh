#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate

echo "Creating superuser if not exists..."
DJANGO_SUPERUSER_PASSWORD=admin123 python manage.py createsuperuser \
    --username admin \
    --email EMAIL_HOST_USER \
    --noinput 2>/dev/null || echo "Superuser already exists, skipping."

echo "Starting Daphne..."
exec daphne -b 0.0.0.0 -p ${PORT:-8000} trading_system.asgi:application
