#!/bin/bash

echo "Running makemigrations for all apps..."
DJANGO_SETTINGS_MODULE=settings.dev python manage.py makemigrations users intern training progress

echo "Running migrate..."
DJANGO_SETTINGS_MODULE=settings.dev python manage.py migrate

echo "Migrations complete."