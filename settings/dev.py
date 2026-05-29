from .base import *

# Paramètres spécifiques au développement
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]'] # Ajoutez d'autres hôtes si nécessaire pour le développement

# Database pour le développement (SQLite par défaut)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Si vous souhaitez utiliser PostgreSQL pour le développement, décommentez et configurez ceci :
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'trainingmanager_dev', # Nom de la base de données de développement
#         'USER' : 'postgres',
#         'PASSWORD' : 'postgres',
#         'HOST' : "localhost",
#         'PORT' : '5432',
#     }
# }