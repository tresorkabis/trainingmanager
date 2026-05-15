from django.core.management import BaseCommand, call_command
from django.db import transaction

from intern.models import Categorie, EtudeStagiaire, Stagiaire
from progress.models import Action, DetailAction, Formateur, TypeAction
from training.models import Filiere, Formation, Service
from users.models import User


class Command(BaseCommand):
    help = "Supprime les donnees de demonstration metier puis relance le seed demo."

    @transaction.atomic
    def handle(self, *args, **options):
        DetailAction.objects.all().delete()
        Action.objects.all().delete()
        Formateur.objects.all().delete()
        TypeAction.objects.all().delete()

        EtudeStagiaire.objects.all().delete()
        Stagiaire.objects.all().delete()
        Categorie.objects.all().delete()

        Formation.objects.all().delete()
        Filiere.objects.all().delete()
        Service.objects.all().delete()

        User.objects.filter(username="demo.manager").delete()

        call_command("seed_demo_data")

        self.stdout.write(self.style.SUCCESS("Reinitialisation et regeneration des donnees de demonstration terminees."))
