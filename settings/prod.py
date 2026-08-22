from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: replace this with your production host(s)!
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'trainingmanager-seven.vercel.app').split(',')

# SECURITY WARNING: La clé secrète doit être définie via une variable d'environnement en production.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-default-key')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'esfor2842749',
        'USER': 'esfor2842749',
        'PASSWORD': 'Tresorkabis@2026',
        'HOST': 'localhost', # Si LWS vous donne un hôte différent, remplacez 'localhost'
        'PORT': '5432',
    }
}

# WhiteNoise pour la production sur Vercel
# On désactive explicitement le stockage WhiteNoise pour éviter tout post-processing qui fait planter Vercel.
# Django utilisera le stockage par défaut qui se contente de copier les fichiers.
STATICFILES_STORAGE = None



