import os
import sys

# Ajouter le chemin du projet au sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Définir la variable d'environnement pour les réglages Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.prod'

# Importer l'application WSGI de Django
from config.wsgi import application
