from .base import *

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'trainingmanager',
#         'USER' : 'postgres',
#         'PASSWORD' : 'postgres',
#         'HOST' : "localhost",
#         'PORT' : '5432',
#     }
# }