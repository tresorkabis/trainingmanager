from django.db import models

from intern.models import Stagiaire
from training.models import Metier # Changé Formation à Metier

class TypeAction(models.Model):
    code = models.CharField(max_length=10, unique=True) # Ajout de unique=True
    libelle = models.CharField(max_length=100)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code + " (" + self.libelle + ")"

class Formateur(models.Model):
    matricule = models.CharField(max_length=10)
    nom = models.CharField(max_length=50)
    postnom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50, blank=True, null=True) # Nouveau champ prénom
    adresse = models.CharField(max_length=50)
    telephone = models.CharField(max_length=15)
    email = models.CharField(max_length=100)
    specialite = models.CharField(max_length=200, blank=True, null=True) # Ajouté précédemment

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom} {self.postnom} {self.prenom or ''}".strip() # Inclure le prénom dans __str__

class Action(models.Model):
    description = models.CharField(max_length=50)
    date_debut = models.DateField()
    date_fin = models.DateField()
    metier = models.ForeignKey(Metier, on_delete=models.CASCADE, related_name="actions") # Changé formation à metier, ajouté related_name
    formateurs = models.ManyToManyField("Formateur", blank=True, related_name="actions")
    type_action = models.ForeignKey(TypeAction, on_delete=models.SET_NULL, null=True, blank=True, related_name="actions_liees") # Nouveau ForeignKey

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id) +"(" + self.description +")"

class DetailAction(models.Model):
    stagiaire = models.ForeignKey(Stagiaire, on_delete=models.CASCADE)
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    statut = models.CharField(max_length=50, default="Inscrit") # Nouveau champ
    date_inscription = models.DateField(auto_now_add=True) # Nouveau champ

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id) +"(" + self.stagiaire.nom + " - " + self.action.metier.nom + ")" # Changé action.formation.nom à action.metier.nom

class Paiement(models.Model):
    MODE_PAIEMENT_CHOICES = [
        ('ESPECES', 'Espèces'),
        ('VIREMENT', 'Virement Bancaire'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('AUTRE', 'Autre'),
    ]

    stagiaire = models.ForeignKey(Stagiaire, on_delete=models.CASCADE, related_name='paiements')
    action = models.ForeignKey(Action, on_delete=models.SET_NULL, null=True, blank=True, related_name='paiements')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField()
    motif = models.CharField(max_length=255, blank=True, null=True)
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, default='ESPECES')
    reference = models.CharField(max_length=100, blank=True, null=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-date_paiement']

    def __str__(self):
        return f"Paiement de {self.montant} pour {self.stagiaire.get_full_name} le {self.date_paiement}"