from .base import *

import dj_database_url
from django.core.exceptions import ImproperlyConfigured


def _env(name, default=""):
    """Lit une variable d'environnement en supprimant les espaces superflus."""
    return os.environ.get(name, default)


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# Sécurité
# ---------------------------------------------------------------------------
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _env_bool("DJANGO_DEBUG", False)

# SECURITY WARNING: la clé secrète DOIT être définie via une variable
# d'environnement en production (recommandé : générer avec
# `python -c "import secrets; print(secrets.token_urlsafe(50))"`).
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "La variable d'environnement DJANGO_SECRET_KEY doit être définie en production."
    )

# Hôtes autorisés, séparés par des virgules.
# Exemple : "trainingmanager-seven.vercel.app,www.mon-domaine.com"
ALLOWED_HOSTS = [h.strip() for h in _env("ALLOWED_HOSTS").split(",") if h.strip()]

# Origines de confiance pour la protection CSRF (HTTPS).
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in _env("CSRF_TRUSTED_ORIGINS").split(",") if o.strip()
]

# ---------------------------------------------------------------------------
# Base de données : Supabase (PostgreSQL)
# ---------------------------------------------------------------------------
# En production serverless (Vercel), utiliser l'URL de connexion Supabase en
# "Transaction mode pooler" (port 6543, host aws-<region>.pooler.supabase.com),
# recommandé officiellement pour les fonctions serverless / courtes connexions.
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ImproperlyConfigured(
        "La variable d'environnement DATABASE_URL doit être définie "
        "(URL de connexion Supabase, mode Transaction pooler recommandé)."
    )

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=0,  # pas de connexion réutilisée entre les appels serverless
        conn_health_checks=True,
    )
}

# WhiteNoise pour la production sur Vercel
# On ne définit aucune compression (pas de post-processing) pour ne pas faire
# planter le build Vercel : Django utilise alors le backend de fichiers
# statiques par défaut, qui copie simplement les fichiers.

# ---------------------------------------------------------------------------
# Fichiers médias : Supabase Storage (API compatible S3)
# ---------------------------------------------------------------------------
# Sur Vercel le filesystem est éphémère : les fichiers uploadés (photos,
# bordereaux, PV) doivent être stockés dans Supabase Storage.
SUPABASE_S3_ACCESS_KEY = os.environ.get("SUPABASE_S3_ACCESS_KEY", "")
SUPABASE_S3_SECRET_KEY = os.environ.get("SUPABASE_S3_SECRET_KEY", "")

if SUPABASE_S3_ACCESS_KEY and SUPABASE_S3_SECRET_KEY:
    INSTALLED_APPS.append("storages")

    SUPABASE_PROJECT_REF = os.environ.get("SUPABASE_PROJECT_REF", "")
    SUPABASE_S3_ENDPOINT = os.environ.get("SUPABASE_S3_ENDPOINT", "")

    if not SUPABASE_S3_ENDPOINT:
        if not SUPABASE_PROJECT_REF:
            raise ImproperlyConfigured(
                "SUPABASE_PROJECT_REF (ou SUPABASE_S3_ENDPOINT) est requis "
                "pour utiliser Supabase Storage."
            )
        SUPABASE_S3_ENDPOINT = f"https://{SUPABASE_PROJECT_REF}.supabase.co/storage/v1/s3"

    AWS_STORAGE_BUCKET_NAME = os.environ.get("SUPABASE_S3_BUCKET", "media")
    AWS_ACCESS_KEY_ID = SUPABASE_S3_ACCESS_KEY
    AWS_SECRET_ACCESS_KEY = SUPABASE_S3_SECRET_KEY
    AWS_S3_REGION_NAME = os.environ.get("SUPABASE_S3_REGION", "eu-central-1")
    AWS_S3_ENDPOINT_URL = SUPABASE_S3_ENDPOINT
    AWS_S3_ADDRESSING_STYLE = "path"  # requeru par Supabase S3
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_DEFAULT_ACL = None  # Supabase n'utilise pas les ACL
    AWS_QUERYSTRING_AUTH = False  # bucket public : accès direct sans signature

    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

    # URL publique des fichiers du bucket (servis par la CDN Supabase).
    MEDIA_URL = (
        f"https://{SUPABASE_PROJECT_REF}.supabase.co/storage/v1/object/public/"
        f"{AWS_STORAGE_BUCKET_NAME}/"
    )
else:
    # Sans les variables S3 (ex : test local ou autre environnement), on reste
    # sur le filesystem local — à utiliser uniquement en développement.
    import warnings
    warnings.warn(
        "Supabase Storage non configuré (SUPABASE_S3_ACCESS_KEY / "
        "SUPABASE_S3_SECRET_KEY absents) : les fichiers médias seront stockés "
        "dans le filesystem local, non persisté sur Vercel."
    )



