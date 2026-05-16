from django.db import models

from training.models import Filiere, Formation, Service

class Categorie(models.Model):
    titre = models.CharField(max_length=100)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titre

class Entreprise(models.Model):
    nom = models.CharField(max_length=200)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom

class Stagiaire(models.Model):
    SEXE_CHOISES = (
        ('M','Masculin'),
        ('F','Feminin'),
        ('ND','Non défini'),
    )
    TYPE_PIECE_CHOICES = (
        ('CE', "Carte d'électeur"),
        ('PS', "Passeport"),
        ('PC', "Permis de conduire"),
    )

    nom = models.CharField(max_length=50)
    postnom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    adresse = models.CharField(max_length=50)
    sexe = models.CharField(max_length=2, choices=SEXE_CHOISES)
    telephone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True, unique=True)
    date_naissance = models.DateField(blank=True, null=True)
    lieu_naissance = models.CharField(max_length=100, blank=True, null=True)
    nationalite = models.CharField(max_length=100, blank=True, null=True)
    type_piece = models.CharField(max_length=2, choices=TYPE_PIECE_CHOICES, blank=True, null=True, verbose_name="Type de pièce") # New field
    numero_piece = models.CharField(max_length=50, blank=True, null=True, unique=True)
    nom_pere = models.CharField(max_length=100, blank=True, null=True)
    nom_mere = models.CharField(max_length=100, blank=True, null=True)
    niveau_etude = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to='stagiaires/', blank=True, null=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE)
    # Removed service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    # Removed filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, null=True, blank=True)

    # New fields for "dans l'emploi" category
    entreprise = models.ForeignKey(Entreprise, on_delete=models.SET_NULL, null=True, blank=True)
    fonction = models.CharField(max_length=100, blank=True, null=True)
    anciennete_emploi = models.IntegerField(blank=True, null=True, verbose_name="Ancienneté dans l'emploi (années)")
    anciennete_entreprise = models.IntegerField(blank=True, null=True, verbose_name="Ancienneté dans l'entreprise (années)")

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom +"(" + self.postnom +")" 


class EtudeStagiaire(models.Model):
    stagiaire = models.ForeignKey(
        Stagiaire,
        on_delete=models.CASCADE,
        related_name='etudes'
    )
    intitule = models.CharField(max_length=150)
    etablissement = models.CharField(max_length=150, blank=True, null=True)
    niveau = models.CharField(max_length=100, blank=True, null=True)
    annee_debut = models.PositiveIntegerField(blank=True, null=True)
    annee_fin = models.PositiveIntegerField(blank=True, null=True)
    diplome_obtenu = models.CharField(max_length=150, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.stagiaire.nom} ({self.intitule})"

class AutreFormation(models.Model):
    stagiaire = models.ForeignKey(
        Stagiaire,
        on_delete=models.CASCADE,
        related_name='autres_formations'
    )
    intitule = models.CharField(max_length=150)
    etablissement = models.CharField(max_length=150, blank=True, null=True)
    annee_fin = models.PositiveIntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.stagiaire.nom} ({self.intitule})"
