#!/bin/bash
# Script de déploiement pour PythonAnywhere
# À exécuter après le push sur le dépôt

echo "=== Déploiement sur PythonAnywhere ==="

# 1. Mettre à jour le code source
git pull origin main

# 2. Activer l'environnement virtuel
source /home/yourusername/.virtualenvs/yourvirtualenv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Collecter les fichiers statiques
python manage.py collectstatic --noinput

# NOTE : settings.prod exige les variables d'environnement suivantes
# (définies dans le panneau PythonAnywhere > Web > Environment variables) :
#   DJANGO_SECRET_KEY=<clé secrète forte>
#   DATABASE_URL=<URL PostgreSQL, ex : chaîne Supabase ou base PythonAnywhere>
# (optionnel, fichiers médias sur Supabase Storage)
#   SUPABASE_PROJECT_REF / SUPABASE_S3_ACCESS_KEY / SUPABASE_S3_SECRET_KEY

# 5. Appliquer les migrations
python manage.py migrate

# 6. Redémarrer l'application web
touch /var/www/yourusername_pythonanywhere_com_wsgi.py

echo "=== Déploiement terminé ==="