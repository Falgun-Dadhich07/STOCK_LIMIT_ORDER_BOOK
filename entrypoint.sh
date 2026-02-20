#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate

echo "Creating superuser if not exists..."
python manage.py shell <<EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'falgund24@iitk.ac.in', 'admin123')
    print('Superuser created successfully!')
else:
    print('Superuser already exists, skipping.')
EOF

echo "Starting Daphne..."
exec daphne -b 0.0.0.0 -p ${PORT:-8000} trading_system.asgi:application
