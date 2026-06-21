from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: replace this with your production host(s)!
ALLOWED_HOSTS = ['tresorkabis.pythonanywhere.com']


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# WhiteNoise with cache busting pour la production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
