from django.db import models

class Categorie(models.Model):
    titre = models.CharField(max_length=100)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titre

class Stagiaire(models.Model):
    SEXE_CHOISES = (
        ('M','Masculin'),
        ('F','Feminin'),
        ('ND','Non défini'),
    )
    nom = models.CharField(max_length=50)
    postnom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    adresse = models.CharField(max_length=50)
    sexe = models.CharField(max_length=2, choices=SEXE_CHOISES)
    telephone = models.CharField(max_length=15)
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE)
    active= models.BooleanField(default=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom +"(" + self.postnom +")" 