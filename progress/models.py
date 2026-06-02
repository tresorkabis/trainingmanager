from django.db import models
import datetime # Importez le module datetime
import random   # Importez le module random
import string   # Importez le module string
from django.db.models import Max # Import Max pour la logique de référence

from intern.models import Stagiaire
from training.models import Formation

class TypeAction(models.Model):
    code = models.CharField(max_length=10, unique=True)
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
    prenom = models.CharField(max_length=50, blank=True, null=True)
    adresse = models.CharField(max_length=50)
    telephone = models.CharField(max_length=15)
    email = models.CharField(max_length=100)
    specialite = models.CharField(max_length=200, blank=True, null=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom} {self.postnom} {self.prenom or ''}".strip()

class Action(models.Model):
    description = models.CharField(max_length=50)
    date_debut = models.DateField()
    date_fin = models.DateField()
    metier = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="actions")
    formateurs = models.ManyToManyField("Formateur", blank=True, related_name="actions")
    type_action = models.ForeignKey(TypeAction, on_delete=models.SET_NULL, null=True, blank=True, related_name="actions_liees")

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id) +"(" + self.description +")"

class DetailAction(models.Model):
    stagiaire = models.ForeignKey(Stagiaire, on_delete=models.CASCADE)
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    statut = models.CharField(max_length=50, default="Inscrit")
    date_inscription = models.DateField(auto_now_add=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id) +"(" + self.stagiaire.nom + " - " + self.action.metier.nom + ")"


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
    # Changement du champ reference en CharField
    reference = models.CharField(max_length=10, unique=True, blank=True, null=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-date_paiement']

    def __str__(self):
        return f"Paiement de {self.montant} pour {self.stagiaire.get_full_name} le {self.date_paiement}"

    def save(self, *args, **kwargs):
        if not self.reference: # Générer la référence seulement si elle n'est pas déjà définie
            # Construire la base de la référence
            stagiaire_initials = ""
            if self.stagiaire:
                # Utilise les premières lettres du nom et prénom du stagiaire
                nom_initial = self.stagiaire.nom[0] if self.stagiaire.nom else ''
                prenom_initial = self.stagiaire.prenom[0] if self.stagiaire.prenom else ''
                stagiaire_initials = (nom_initial + prenom_initial).upper()[:2] # Max 2 initiales

            date_part = ""
            if self.date_paiement:
                date_part = self.date_paiement.strftime('%y%m%d') # YYMMDD (6 caractères)
            else:
                date_part = datetime.date.today().strftime('%y%m%d') # Date du jour si non spécifiée

            base_ref = f"{stagiaire_initials}{date_part}" # Max 2 + 6 = 8 caractères

            # Assurer l'unicité avec un suffixe
            suffix_len = 10 - len(base_ref) # Caractères restants pour le suffixe
            if suffix_len < 1: # Si la base est déjà trop longue, la tronquer
                base_ref = base_ref[:9]
                suffix_len = 1

            counter = 0
            while True:
                suffix = ""
                if counter > 0:
                    # Utilise des chiffres puis des lettres pour le suffixe
                    if counter < 10:
                        suffix = str(counter)
                    elif counter < 36: # A-Z pour 10-35
                        suffix = string.ascii_uppercase[counter - 10]
                    else: # Au-delà, utilise un petit aléatoire
                        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=suffix_len))
                
                potential_ref = (base_ref + suffix).upper()
                potential_ref = potential_ref[:10] # Tronquer à 10 caractères max

                if not Paiement.objects.filter(reference=potential_ref).exists():
                    self.reference = potential_ref
                    break
                counter += 1
                if counter > 100: # Mesure de sécurité pour éviter une boucle infinie en cas de collisions extrêmes
                    # Fallback vers une référence plus aléatoire si trop de collisions
                    self.reference = 'PAY' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))[:10]
                    break

        super().save(*args, **kwargs)