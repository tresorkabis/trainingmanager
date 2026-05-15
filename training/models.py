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
    fraismateriels = models.FloatField(verbose_name="Frais matériels", default=0.0)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom
