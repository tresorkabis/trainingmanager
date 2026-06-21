#!/bin/bash

# Activer l'environnement virtuel du projet
# Le script suppose que le répertoire .venv se trouve à la racine du projet.
if [ -f "$(dirname "$0")/.venv/bin/activate" ]; then
    source "$(dirname "$0")/.venv/bin/activate"
else
    echo "Environnement virtuel non trouvé. Veuillez créer .venv ou ajuster le chemin."
    exit 1
fi

# Supprimer les anciennes migrations (sauf __init__.py)
echo "Removing old migration files..."
find . -type f -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -type d -path "*/migrations/__pycache__" -exec rm -r {} +

echo "Running makemigrations for all apps..."
DJANGO_SETTINGS_MODULE=settings.prod python manage.py makemigrations users intern training progress

echo "Running migrate..."
DJANGO_SETTINGS_MODULE=settings.prod python manage.py migrate

echo "Migrations complete."
