from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q, F
from decimal import Decimal
import datetime as dt
from datetime import timedelta
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

    def get_full_name(self):
        return f"{self.nom} {self.postnom} {self.prenom or ''}".strip()

class Action(models.Model):
    DAY_OF_WEEK_CHOICES = [
        (0, "Lundi"),
        (1, "Mardi"),
        (2, "Mercredi"),
        (3, "Jeudi"),
        (4, "Vendredi"),
        (5, "Samedi"),
        (6, "Dimanche"),
    ]

    STATUT_CHOICES = [
        ('PLANIFIEE', 'Planifiée'),
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
        ('ANNULEE', 'Annulée'),
    ]

    description = models.CharField(max_length=150)
    date_debut = models.DateField()
    date_fin = models.DateField()
    formation = models.ForeignKey(Formation, on_delete=models.PROTECT, related_name="actions")
    formateurs = models.ManyToManyField("Formateur", blank=True, related_name="actions")
    type_action = models.ForeignKey(TypeAction, on_delete=models.SET_NULL, null=True, blank=True, related_name="actions_liees")
    lieu = models.CharField(max_length=100, blank=True, null=True) # Nouveau champ lieu
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='PLANIFIEE') # Nouveau champ statut

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(date_debut__lte=F("date_fin")),
                name="action_date_range_valid",
            )
        ]

    def __str__(self):
        return str(self.id) +"(" + self.description +")"

    def update_statut(self):
        total_modules = self.formation.modules.count()
        if total_modules == 0:
            return False

        # Récupère les statuts des modules (un seul par module, même s'il y a plusieurs formateurs)
        module_statuses = {
            entry['module']: entry['statut_module']
            for entry in self.module_progressions.values('module', 'statut_module')
        }

        # Si tous les modules sont terminés ou validés → TERMINEE
        completed_count = sum(1 for s in module_statuses.values() if s in ('TE', 'VA'))
        if completed_count >= total_modules:
            if self.statut != 'TERMINEE':
                self.statut = 'TERMINEE'
                self.save(update_fields=['statut', 'updated_at'])
            return True

        # Si au moins un module est en cours → EN_COURS
        in_progress_count = sum(1 for s in module_statuses.values() if s == 'EC')
        if in_progress_count > 0:
            if self.statut != 'EN_COURS':
                self.statut = 'EN_COURS'
                self.save(update_fields=['statut', 'updated_at'])
            return True

        # Sinon, au moins un module est non commencé ou en échec → PLANIFIEE
        if self.statut != 'PLANIFIEE':
            self.statut = 'PLANIFIEE'
            self.save(update_fields=['statut', 'updated_at'])
        return True

    def clean(self):
        super().clean()
        if self.date_debut and self.date_fin and self.date_fin < self.date_debut:
            raise ValidationError({
                "date_fin": "La date de fin doit être postérieure ou égale à la date de début."
            })

    def get_course_schedules(self):
        return self.course_schedules.all().order_by("jour_semaine", "heure_debut", "ordre", "id")

    def get_course_schedule_summary(self):
        schedules = []
        for schedule in self.get_course_schedules():
            schedules.append(
                f"{schedule.get_jour_semaine_display()} {schedule.heure_debut.strftime('%H:%M')} - {schedule.heure_fin.strftime('%H:%M')}"
            )
        return " | ".join(schedules)

    def get_next_course_schedule(self, after_date=None):
        schedules = list(self.get_course_schedules())
        if not schedules:
            return None, None

        if after_date is None:
            after_date = self.date_debut - timedelta(days=1)

        candidates = []
        for schedule in schedules:
            candidate_date = schedule.get_next_occurrence(after_date)
            candidates.append((candidate_date, schedule.heure_debut, schedule.id or 0, schedule))

        candidate_date, _, _, schedule = min(candidates, key=lambda item: (item[0], item[1], item[2]))
        return schedule, candidate_date

    def matches_course_schedule(self, course_date, start_time=None, end_time=None):
        weekday = course_date.weekday()
        for schedule in self.get_course_schedules():
            if schedule.jour_semaine != weekday:
                continue
            if start_time and start_time < schedule.heure_debut:
                continue
            if end_time and end_time > schedule.heure_fin:
                continue
            return schedule
        return None

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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


class ActionSchedule(models.Model):
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name="course_schedules")
    jour_semaine = models.PositiveSmallIntegerField(choices=Action.DAY_OF_WEEK_CHOICES)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    ordre = models.PositiveSmallIntegerField(default=1)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Créneau de cours"
        verbose_name_plural = "Créneaux de cours"
        ordering = ["jour_semaine", "heure_debut", "ordre", "id"]
        constraints = [
            models.CheckConstraint(
                check=Q(heure_debut__lt=F("heure_fin")),
                name="action_schedule_time_range_valid",
            ),
            models.UniqueConstraint(
                fields=["action", "jour_semaine", "heure_debut", "heure_fin"],
                name="action_schedule_unique_slot",
            ),
        ]

    def __str__(self):
        return (
            f"{self.action.description} - {self.get_jour_semaine_display()} "
            f"{self.heure_debut.strftime('%H:%M')} - {self.heure_fin.strftime('%H:%M')}"
        )

    def clean(self):
        super().clean()
        if self.heure_debut and self.heure_fin and self.heure_fin <= self.heure_debut:
            raise ValidationError({
                "heure_fin": "L'heure de fin doit être postérieure à l'heure de début."
            })

    def get_next_occurrence(self, after_date):
        days_ahead = (self.jour_semaine - after_date.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return after_date + timedelta(days=days_ahead)


class ModuleProgress(models.Model):
    STATUT_CHOICES = (
        ('NC', 'Non commencé'),
        ('EC', 'En cours'),
        ('TE', 'Terminé'),
        ('VA', 'Validé'),
        ('EF', 'Échec'), # Changed 'EC' to 'EF' to avoid conflict with 'En cours'
    )
    formateur = models.ForeignKey(Formateur, on_delete=models.PROTECT, related_name='module_progressions')
    action = models.ForeignKey(Action, on_delete=models.PROTECT, related_name='module_progressions')
    module = models.ForeignKey(Module, on_delete=models.PROTECT)
    date_debut_reelle = models.DateField(blank=True, null=True)
    date_fin_reelle = models.DateField(blank=True, null=True)
    statut_module = models.CharField(max_length=2, choices=STATUT_CHOICES, default='NC')
    note = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    commentaires = models.TextField(blank=True, null=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('formateur', 'action', 'module') # Updated unique_together
        ordering = ['action__date_debut', 'module__ordre', 'formateur__nom'] # Updated ordering
        verbose_name = "Progression du Module"
        verbose_name_plural = "Progression des Modules"
        constraints = [
            models.CheckConstraint(
                check=Q(date_debut_reelle__lte=F("date_fin_reelle")),
                name="module_progress_date_range_valid",
            ),
        ]

    def __str__(self):
        return f"Progression de {self.formateur.get_full_name()} pour {self.module.titre} dans {self.action.description} ({self.get_statut_module_display()})"

    def update_statut_module(self):
        hours_done = self.calculate_hours_done()
        if hours_done >= self.module.duree_heures:
            new_statut = 'TE'
        elif hours_done > 0:
            new_statut = 'EC'
        else:
            new_statut = 'NC'
        if self.statut_module != new_statut:
            self.statut_module = new_statut
            self.save(update_fields=['statut_module', 'updated_at'])

    def calculate_hours_done(self):
        import datetime as dt
        total = 0
        for s in self.sessions_progress.filter(statut='REALISEE'):
            if s.actual_start_time and s.actual_end_time:
                start = dt.datetime.combine(dt.date.today(), s.actual_start_time)
                end = dt.datetime.combine(dt.date.today(), s.actual_end_time)
                total += (end - start).total_seconds() / 3600
        return round(total, 1)

    def update_statut_module(self):
        hours_done = self.calculate_hours_done()
        if hours_done >= self.module.duree_heures:
            new_statut = 'TE'
        elif hours_done > 0:
            new_statut = 'EC'
        else:
            new_statut = 'NC'
        if self.statut_module != new_statut:
            self.statut_module = new_statut
            self.save(update_fields=['statut_module', 'updated_at'])

    def clean(self):
        super().clean()
        errors = {}

        if self.action_id and self.module_id and self.action.formation_id != self.module.formation_id:
            errors["module"] = "Le module doit appartenir à la même formation que l'action."

        if self.date_debut_reelle and self.date_fin_reelle and self.date_fin_reelle < self.date_debut_reelle:
            errors["date_fin_reelle"] = "La date de fin réelle doit être postérieure ou égale à la date de début réelle."

        if errors:
            raise ValidationError(errors)

    def get_subject_planning(self):
        subjects = list(self.module.subjects.filter(active=True).order_by("ordre", "id"))
        if not subjects:
            return None

        consumed_sessions = self.sessions_progress.exclude(statut="ANNULEE").count()
        remaining = consumed_sessions

        for subject in subjects:
            sessions_for_subject = max(subject.nombre_seances, 1)
            if remaining < sessions_for_subject:
                return {
                    "subject": subject,
                    "session_index": remaining + 1,
                    "sessions_for_subject": sessions_for_subject,
                }
            remaining -= sessions_for_subject

        subject = subjects[-1]
        return {
            "subject": subject,
            "session_index": subject.nombre_seances,
            "sessions_for_subject": subject.nombre_seances,
        }

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.update_statut_module()
        if self.action_id:
            self.action.update_statut()

    def delete(self, *args, **kwargs):
        if self.sessions_progress.exists():
            raise ValidationError("Impossible de supprimer cette progression car des séances y sont rattachées.")
        super().delete(*args, **kwargs)


class ModuleSubject(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="subjects")
    titre = models.CharField(max_length=200)
    nombre_seances = models.PositiveSmallIntegerField(default=1, verbose_name="Nombre de séances")
    ordre = models.PositiveSmallIntegerField(default=1)
    description = models.TextField(blank=True, null=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sujet du module"
        verbose_name_plural = "Sujets du module"
        ordering = ["ordre", "id"]
        constraints = [
            models.CheckConstraint(
                check=Q(nombre_seances__gte=1),
                name="module_subject_sessions_minimum",
            ),
            models.UniqueConstraint(
                fields=["module", "ordre"],
                name="module_subject_unique_order",
            ),
        ]

    def __str__(self):
        return f"{self.module.titre} - {self.titre}"

class SessionProgress(models.Model):
    STATUT_CHOICES = (
        ('PLANIFIEE', 'Planifiée'),
        ('REALISEE', 'Réalisée'),
        ('REPORTEE', 'Reportée'),
        ('ANNULEE', 'Annulée'),
    )

    module_progress = models.ForeignKey(ModuleProgress, on_delete=models.PROTECT, related_name='sessions_progress')
    planned_date = models.DateField(blank=True, null=True, verbose_name="Date prévue")
    planned_start_time = models.TimeField(blank=True, null=True, verbose_name="Heure prévue de début")
    planned_end_time = models.TimeField(blank=True, null=True, verbose_name="Heure prévue de fin")
    planned_topics = models.TextField(blank=True, null=True, verbose_name="Sujets prévus")
    actual_date = models.DateField(blank=True, null=True, verbose_name="Date réelle")
    actual_start_time = models.TimeField(blank=True, null=True, verbose_name="Heure réelle de début")
    actual_end_time = models.TimeField(blank=True, null=True, verbose_name="Heure réelle de fin")
    topics_covered = models.TextField(blank=True, null=True, verbose_name="Sujets couverts")
    formateur = models.ForeignKey(Formateur, on_delete=models.PROTECT, null=True, blank=True, related_name='sessions_animees')
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='PLANIFIEE')
    notes = models.TextField(blank=True, null=True, verbose_name="Notes additionnelles")

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Progression de la Séance"
        verbose_name_plural = "Progression des Séances"
        ordering = ['planned_date', 'actual_date', 'planned_start_time']
        constraints = [
            models.CheckConstraint(
                check=Q(planned_start_time__lte=F("planned_end_time")),
                name="session_progress_planned_time_range_valid",
            ),
            models.CheckConstraint(
                check=Q(actual_start_time__lte=F("actual_end_time")),
                name="session_progress_actual_time_range_valid",
            ),
        ]

    def __str__(self):
        display_date = self.actual_date or self.planned_date
        return f"Séance du {display_date} pour {self.module_progress.module.titre} par {self.formateur or 'N/A'}"

    def clean(self):
        super().clean()
        errors = {}

        if self.planned_start_time and self.planned_end_time and self.planned_end_time < self.planned_start_time:
            errors["planned_end_time"] = "L'heure prévue de fin doit être postérieure ou égale à l'heure prévue de début."

        if not self.planned_date:
            errors["planned_date"] = "La date prévue est obligatoire."

        if self.actual_start_time and self.actual_end_time and self.actual_end_time < self.actual_start_time:
            errors["actual_end_time"] = "L'heure réelle de fin doit être postérieure ou égale à l'heure réelle de début."

        if self.module_progress_id and self.planned_date:
            action = self.module_progress.action
            if action and (self.planned_date < action.date_debut or self.planned_date > action.date_fin):
                errors["planned_date"] = "La séance prévue doit se situer entre les dates de début et de fin de l'action."
            if action and action.course_schedules.exists():
                matched_schedule = action.matches_course_schedule(
                    self.planned_date,
                    self.planned_start_time,
                    self.planned_end_time,
                )
                if not matched_schedule:
                    errors["planned_date"] = "La séance prévue doit respecter un créneau de cours de l'action."
                    if self.planned_start_time:
                        errors["planned_start_time"] = "L'heure prévue doit correspondre à un créneau de cours de l'action."
                    if self.planned_end_time:
                        errors["planned_end_time"] = "L'heure prévue doit correspondre à un créneau de cours de l'action."

        if self.module_progress_id and self.actual_date:
            action = self.module_progress.action
            # On ne bloque plus la date réelle, on permet le dépassement (rattrapage)
            # Mais on pourrait logguer ou flagger l'anomalie ici si besoin.
            pass

        if self.module_progress_id and self.formateur_id and self.formateur_id != self.module_progress.formateur_id:
            errors["formateur"] = "Le formateur de la séance doit correspondre au formateur de la progression du module."

        if self.statut == "REALISEE" and not self.actual_date:
            errors["actual_date"] = "La date réelle est obligatoire pour une séance réalisée."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Assigne automatiquement le formateur du module si non défini
        if not self.formateur and self.module_progress:
            self.formateur = self.module_progress.formateur

        self.full_clean()
        super().save(*args, **kwargs)
        self.module_progress.update_statut_module()



class FormateurPerformance(models.Model):
    formateur = models.ForeignKey(Formateur, on_delete=models.CASCADE, related_name='performances')
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name='formateur_performances')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='seances')
    
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
        verbose_name = "Séance du Formateur"
        verbose_name_plural = "Séances des Formateurs"
        ordering = ['action__date_debut', 'module__ordre', 'date_debut_reelle', 'formateur__nom']

    def __str__(self):
        return f"Séance de {self.formateur} pour {self.action.description} - {self.module.titre}"


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
                date_part = dt.date.today().strftime('%y%m%d') # Date du jour si non spécifiée

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
