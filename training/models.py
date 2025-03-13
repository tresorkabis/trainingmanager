from django.db import models

class Filiere(models.Model):
    nom = models.CharField(max_length=200)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom
    
class Formation(models.Model):
    nom = models.CharField(max_length=200)
    duree = models.IntegerField(default=0)
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, null=True, blank=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom
