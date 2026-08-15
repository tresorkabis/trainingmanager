from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: replace this with your production host(s)!
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'tresorkabis.pythonanywhere.com').split(',')

# SECURITY WARNING: La clé secrète doit être définie via une variable d'environnement en production.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-default-key')

# Database
# Utilisation de dj-database-url pour récupérer la configuration depuis la variable DATABASE_URL de Render
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}

# WhiteNoise with cache busting pour la production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
