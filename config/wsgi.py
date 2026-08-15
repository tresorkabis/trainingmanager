"""
WSGI project for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from django.core.management import call_command

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.prod')

# Force migration and admin creation on startup for Free Tier deployments
try:
    print("Running migrations...")
    call_command('migrate', interactive=False)
    print("Creating admin user...")
    from django.contrib.auth import get_user_model; User = get_user_model()
    User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'demo')
    print("Migrations and admin creation completed successfully.")
except Exception as e:
    print(f"Error during startup migration: {e}")

application = get_wsgi_application()
