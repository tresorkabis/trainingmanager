from django.core.management import BaseCommand

from users.utils import createprofile

class Command(BaseCommand):
    def handle(self, *args, **options):
        createprofile()