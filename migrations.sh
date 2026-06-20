#!/bin/bash

# Supprimer les anciennes migrations (sauf __init__.py)
echo "Removing old migration files..."
find . -type f -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -type d -path "*/migrations/__pycache__" -exec rm -r {} +

echo "Running makemigrations for all apps..."
DJANGO_SETTINGS_MODULE=settings.dev python manage.py makemigrations users intern training progress

echo "Running migrate..."
DJANGO_SETTINGS_MODULE=settings.dev python manage.py migrate

echo "Migrations complete."