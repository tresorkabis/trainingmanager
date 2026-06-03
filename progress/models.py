from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal
import datetime # Importez le module datetime
import random   # Importez le module random
import string   # Importez le module string
from django.db.models import Max # Import Max pour la logique de référence

from intern.models import Stagiaire
from training.models import Formation, Module # Import Module
from users.models import User # Import User pour l'évaluateur

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
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="actions")
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
        return str(self.id) +"(" + self.stagiaire.nom + " - " + self.action.formation.nom + ")"

class ModuleProgress(models.Model):
    STATUT_CHOICES = (
        ('NC', 'Non commencé'),
        ('EC', 'En cours'),
        ('TE', 'Terminé'),
        ('VA', 'Validé'),
        ('EC', 'Échec'),
    )
    detail_action = models.ForeignKey(DetailAction, on_delete=models.CASCADE, related_name='modules_progress')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    date_debut_reelle = models.DateField(blank=True, null=True)
    date_fin_reelle = models.DateField(blank=True, null=True)
    statut_module = models.CharField(max_length=2, choices=STATUT_CHOICES, default='NC')
    note = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    commentaires = models.TextField(blank=True, null=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('detail_action', 'module') # Un stagiaire ne peut avoir qu'une progression par module et par action
        ordering = ['module__ordre']

    def __str__(self):
        return f"{self.detail_action.stagiaire.get_full_name()} - {self.module.titre} ({self.get_statut_module_display()})"

class FormateurPerformance(models.Model):
    formateur = models.ForeignKey(Formateur, on_delete=models.CASCADE, related_name='performances')
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name='formateur_performances')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    
    # Dates prévues (issues du module de la formation)
    # date_debut_previsionnelle = models.DateField() # Ces dates seront dérivées du module lui-même ou de l'action
    # date_fin_previsionnelle = models.DateField()   # Pas besoin de les stocker ici si elles sont fixes par module/action

    # Dates réelles de prestation
    date_debut_reelle = models.DateField(blank=True, null=True, verbose_name="Date réelle de début")
    date_fin_reelle = models.DateField(blank=True, null=True, verbose_name="Date réelle de fin")
    heures_effectuees = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Heures effectuées")

    # Évaluation de la prestation
    date_evaluation = models.DateField(blank=True, null=True, verbose_name="Date d'évaluation")
    evaluateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='evaluations_formateurs')
    note_pedagogique = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True, verbose_name="Note pédagogique (0-5)")
    note_contenu = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True, verbose_name="Note contenu (0-5)")
    note_organisation = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True, verbose_name="Note organisation (0-5)")
    commentaires = models.TextField(blank=True, null=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('formateur', 'action', 'module')
        verbose_name = "Performance du Formateur"
        verbose_name_plural = "Performances des Formateurs"
        ordering = ['action__date_debut', 'module__ordre', 'formateur__nom']

    def __str__(self):
        return f"Performance de {self.formateur.get_full_name()} pour {self.action.description} - {self.module.titre}"


class Paiement(models.Model):
    MODE_PAIEMENT_CHOICES = [
        ('ESPECES', 'Espèces'),
        ('VIREMENT', 'Virement Bancaire'),
    ]

    stagiaire = models.ForeignKey(Stagiaire, on_delete=models.CASCADE, related_name='paiements')
    action = models.ForeignKey(Action, on_delete=models.SET_NULL, null=True, blank=True, related_name='paiements')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField()
    motif = models.CharField(max_length=255, blank=True, null=True)
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, default='ESPECES')
    bordereau_photo = models.ImageField(upload_to="paiements/bordereaux/", blank=True, null=True)
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

    def clean(self):
        super().clean()
        if self.mode_paiement == "VIREMENT" and not self.bordereau_photo:
            raise ValidationError({
                "bordereau_photo": "La photo du bordereau est obligatoire pour un paiement par virement bancaire."
            })

    def get_total_cout(self):
        if self.action and self.action.formation:
            return self.action.formation.cout or Decimal("0.00")
        return None

    def get_total_paye(self):
        if not self.action_id or not self.stagiaire_id:
            return None
        total = Paiement.objects.filter(
            stagiaire_id=self.stagiaire_id,
            action_id=self.action_id,
        ).aggregate(total=Sum("montant"))["total"]
        return total or Decimal("0.00")

    def get_solde_restant(self):
        total_cout = self.get_total_cout()
        total_paye = self.get_total_paye()
        if total_cout is None or total_paye is None:
            return None
        return total_cout - total_paye

    def save(self, *args, **kwargs):
        self.full_clean()
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