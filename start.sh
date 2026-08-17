#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Checking database connection..."
# Simple loop to wait for DB to be ready
until python manage.py migrate --noinput; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "Migrations completed successfully."

# Create admin user if it doesn't exist
echo "Ensuring admin user exists..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'demo')"

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
