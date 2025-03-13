from django.db import models

from intern.models import Stagiaire
from training.models import Formation

class TypeAction(models.Model):
    code = models.CharField(max_length=10)
    libelle = models.CharField(max_length=100)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return self.code + " (" + self.libele + ")"

class Formateur(models.Model):
    matricule = models.CharField(max_length=10)
    nom = models.CharField(max_length=50)
    postnom = models.CharField(max_length=50)
    adresse = models.CharField(max_length=50)
    telephone = models.CharField(max_length=15)
    email = models.CharField(max_length=100)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return self.nom + "(" + self.postnom + ")"

class Action(models.Model):
    description = models.CharField(max_length=50)
    date_debut = models.DateField()
    date_fin = models.DateField()
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return self.code +"(" + self.description +")"

class DetailAction(models.Model):
    stagiaire = models.ForeignKey(Stagiaire, on_delete=models.CASCADE)
    action = models.ForeignKey(Action, on_delete=models.CASCADE)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return self.stagiaire.nom +"(" + self.action.formation.nom +")"