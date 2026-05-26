#!/bin/bash

echo "Running makemigrations for all apps..."
python manage.py makemigrations users intern training progress

echo "Running migrate..."
python manage.py migrate

echo "Migrations complete."