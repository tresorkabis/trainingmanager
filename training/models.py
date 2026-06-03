from django.db import models
# from progress.models import Formateur # <-- Cette ligne sera supprimée

class Service(models.Model):
    nom = models.CharField(max_length=200)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom

class Filiere(models.Model):
    nom = models.CharField(max_length=200)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name="filieres") # Ajout de related_name

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom
    
# Le modèle Formateur est défini dans progress.models, nous n'avons pas besoin de le définir ici.

class Formation(models.Model): # Renommé de Metier à Formation
    TYPE_CHOICES = (
        ("qualifiante", "Qualifiante"),
        ("continue", "Continue"),
    )

    nom = models.CharField(max_length=200)
    duree = models.IntegerField(default=0)
    duree_heures = models.PositiveIntegerField(default=0, verbose_name="Durée en heures")
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, null=True, blank=True, related_name="formations") # Changé related_name de metiers à formations
    cout = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Coût")
    type_formation = models.CharField(max_length=20, choices=TYPE_CHOICES, default="qualifiante", verbose_name="Type de formation") # Nouveau champ
    
    # Champs de frais ajoutés/modifiés
    frais_participation = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Frais de participation")
    frais_jury = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Frais du jury")
    frais_materiels = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Frais matériels") # Renommé et type ajusté

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom


class Module(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="modules") # Changé de metier à formation
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    duree_heures = models.PositiveIntegerField(default=0, verbose_name="Durée en heures")
    formateurs = models.ManyToManyField('progress.Formateur', related_name="modules_dispenses", blank=True)
    ordre = models.PositiveIntegerField(default=1)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ordre", "id"]

    def __str__(self):
        return f"{self.formation.nom} - {self.titre}" # Changé de metier.nom à formation.nom