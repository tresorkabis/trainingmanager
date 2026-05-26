from django.db import models

class Service(models.Model):
    nom = models.CharField(max_length=200)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom

class Filiere(models.Model):
    nom = models.CharField(max_length=200)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom
    
class Formation(models.Model):
    nom = models.CharField(max_length=200)
    duree = models.IntegerField(default=0)
    duree_heures = models.PositiveIntegerField(default=0, verbose_name="Durée en heures")
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, null=True, blank=True)
    cout = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Coût")
    
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
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="modules")
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    duree_heures = models.PositiveIntegerField(default=0, verbose_name="Durée en heures")
    ordre = models.PositiveIntegerField(default=1)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ordre", "id"]

    def __str__(self):
        return f"{self.formation.nom} - {self.titre}"
