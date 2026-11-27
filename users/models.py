from django.db import models
from django.contrib.auth.models import AbstractUser
from training.models import Filiere, Service # Importation des modèles Filiere et Service

DEFAULT_INSTITUTION_NAME = "École Supérieure de Formation des Cadres"
DEFAULT_INSTITUTION_ACRONYM = "ESFORCA"


class InstitutionSettings(models.Model):
    """Identité de l'institut utilisée dans les documents imprimés."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    institution_name = models.CharField(
        "Nom officiel de l'institut",
        max_length=200,
        default=DEFAULT_INSTITUTION_NAME,
    )
    institution_acronym = models.CharField(
        "Sigle de l’institut",
        max_length=50,
        default=DEFAULT_INSTITUTION_ACRONYM,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Réglage de l'institut"
        verbose_name_plural = "Réglages de l'institut"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.institution_acronym} — {self.institution_name}"


class Profile(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    email = models.EmailField(max_length=255, unique=True, null=True) # Changé CharField à EmailField
    password = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    profile = models.ForeignKey(Profile, on_delete=models.DO_NOTHING, blank=True, null=True)
    photo_url = models.ImageField(upload_to='photos/', blank=True, null=True)

    # Nouveaux champs pour l'association aux filières et services
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)

    REQUIRED_FIELDS = []
