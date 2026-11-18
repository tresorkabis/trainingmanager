from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django_select2.forms import Select2Widget # Importez Select2Widget
from .models import Paiement, Stagiaire, Formateur, ModuleProgress, SessionProgress, DetailAction, JuryPV, JuryNote # Added JuryPV, JuryNote
from training.models import Module # Import Module
from users.models import User # Import User pour le formulaire

class PaiementForm(forms.ModelForm):
    # Permet de filtrer les stagiaires et actions si nécessaire, ou de les afficher tous
    stagiaire = forms.ModelChoiceField(
        queryset=Stagiaire.objects.all().order_by('nom', 'postnom', 'prenom'), # Ordonner pour une meilleure UX
        label="Stagiaire",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'}) # Ajout des classes pour Select2
    )
    from .models import Action
    action = forms.ModelChoiceField(
        queryset=Action.objects.all().order_by('description'), # Ordonner pour une meilleure UX
        required=False,
        label="Action de formation",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'}) # Ajout des classes pour Select2
    )
    date_paiement = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label="Date du paiement") # Ajout de la classe ici
    bordereau_photo = forms.ImageField(
        required=False,
        label="Photo du bordereau",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Paiement
        fields = ['stagiaire', 'action', 'montant', 'date_paiement', 'motif', 'mode_paiement', 'bordereau_photo']
        labels = {
            'montant': 'Montant',
            'motif': 'Motif',
            'mode_paiement': 'Mode de paiement',
        }
        widgets = {
            'montant': forms.NumberInput(attrs={'class': 'form-control'}), # Ajout de la classe pour montant
            'motif': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        eligible_stagiaires = Stagiaire.objects.exclude(
            categorie__titre__iexact="dans l'emploi"
        )
        if self.instance and self.instance.pk and self.instance.stagiaire_id:
            eligible_stagiaires = Stagiaire.objects.filter(
                Q(categorie__titre__iexact="dans l'emploi") & Q(pk=self.instance.stagiaire_id)
            ) | eligible_stagiaires
        self.fields['stagiaire'].queryset = eligible_stagiaires.order_by('nom', 'postnom', 'prenom')
        # L'action de formation doit être liée au stagiaire : on ne propose que les
        # actions auxquelles le stagiaire est inscrit (DetailAction). Ce filtre est
        # appliqué côté serveur lors d'un POST ou d'une modification.
        from progress.models import DetailAction, Action
        stagiaire_id = None
        if self.data.get('stagiaire'):
            try:
                stagiaire_id = int(self.data.get('stagiaire'))
            except (TypeError, ValueError):
                stagiaire_id = None
        if stagiaire_id is None and self.instance and self.instance.pk and self.instance.stagiaire_id:
            stagiaire_id = self.instance.stagiaire_id
        if stagiaire_id:
            action_ids = DetailAction.objects.filter(
                stagiaire_id=stagiaire_id
            ).values_list('action_id', flat=True).distinct()
            self.fields['action'].queryset = Action.objects.filter(
                pk__in=action_ids
            ).order_by('description')

# Removed FormateurPerformanceForm class

class ModuleProgressForm(forms.ModelForm):
    formateur = forms.ModelChoiceField(
        queryset=Formateur.objects.all().order_by('nom', 'postnom'),
        label="Formateur",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )
    from .models import Action
    action = forms.ModelChoiceField(
        queryset=Action.objects.all().order_by('description'),
        label="Action de formation",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )
    module = forms.ModelChoiceField(
        queryset=Module.objects.all().order_by('formation__nom', 'ordre'),
        label="Module",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'}),
        help_text="Sélectionnez le module concerné par cette progression."
    )
    date_debut_reelle = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date réelle de début",
        required=False
    )
    date_fin_reelle = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date réelle de fin",
        required=False
    )
    statut_module = forms.ChoiceField(
        choices=ModuleProgress.STATUT_CHOICES,
        label="Statut du module",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    note = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        label="Note",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '20'})
    )
    commentaires = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label="Commentaires",
        required=False
    )

    class Meta:
        model = ModuleProgress
        fields = [
            'formateur', 'action', 'module', 'date_debut_reelle', 'date_fin_reelle',
            'statut_module', 'note', 'commentaires'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Action

        action_value = self.data.get('action') or self.initial.get('action')
        if self.instance.pk and not action_value:
            action_value = self.instance.action_id
        action_id = getattr(action_value, 'pk', action_value)
        if action_id:
            try:
                action_obj = Action.objects.get(pk=action_id)
                self.fields['module'].queryset = Module.objects.filter(
                    formation=action_obj.formation
                ).order_by('ordre')
            except (ValueError, TypeError, Action.DoesNotExist):
                pass

        module_value = self.data.get('module') or self.initial.get('module')
        if self.instance.pk and not module_value:
            module_value = self.instance.module_id
        module_id = getattr(module_value, 'pk', module_value)
        if module_id:
            try:
                selected_module = Module.objects.get(pk=module_id)
                self.fields['formateur'].queryset = selected_module.formateurs.filter(
                    active=True
                ).order_by('nom', 'postnom')
            except (ValueError, TypeError, Module.DoesNotExist):
                pass

class SessionProgressForm(forms.ModelForm):
    planned_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date prévue"
    )
    planned_start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Heure prévue de début",
        required=False
    )
    planned_end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Heure prévue de fin",
        required=False
    )
    planned_topics = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label="Sujets prévus",
        required=False
    )
    actual_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date réelle",
        required=False
    )
    actual_start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Heure réelle de début",
        required=False
    )
    actual_end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Heure réelle de fin",
        required=False
    )
    topics_covered = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label="Sujets couverts",
        required=False
    )
    statut = forms.ChoiceField(
        choices=SessionProgress.STATUT_CHOICES,
        label="Statut",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label="Notes additionnelles",
        required=False
    )

    class Meta:
        model = SessionProgress
        fields = [
            'planned_date', 'planned_start_time', 'planned_end_time', 'planned_topics',
            'actual_date', 'actual_start_time', 'actual_end_time', 'topics_covered',
            'statut', 'notes'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply form-control class to all fields by default, if not already set by widget
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (Select2Widget, forms.CheckboxInput, forms.DateInput, forms.TimeInput, forms.Textarea, forms.Select)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select) and 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.DateInput) and 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.TimeInput) and 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})


    def clean(self):
        cleaned_data = super().clean()
        statut = cleaned_data.get('statut')
        topics_covered = cleaned_data.get('topics_covered')

        # Si le statut est 'REALISEE' et que des sujets ont été prévus,
        # vérifier que des sujets couverts ont bien été renseignés
        if statut == 'REALISEE' and not topics_covered and planned_topics:
            # On ajoute une erreur pour inviter à compléter les sujets couverts
            self.add_error('topics_covered', 'Les sujets prévus sont présents mais aucun sujet couvert n\'a été renseigné.')

        return cleaned_data




def clean(self):
        cleaned_data = super().clean()
        statut = cleaned_data.get('statut')
        topics_covered = cleaned_data.get('topics_covered')
        planned_topics = cleaned_data.get('planned_topics')

        # Règle métier : si le statut est 'PLANIFIEE', le champ 'topics_covered' doit être vide
        if statut == 'PLANIFIEE' and topics_covered:
            self.add_error('topics_covered', 'Les sujets couverts doivent être vides pour une séance planifiée.')
            cleaned_data['topics_covered'] = ''

        # Si le statut est 'REALISEE', vérifier que les sujets couverts ne sont pas vides si des sujets prévus existent
        if statut == 'REALISEE' and not topics_covered and planned_topics:
            self.add_error('topics_covered', 'Les sujets prévus sont présents mais aucun sujet couvert n\'a été renseigné.')

        return cleaned_data


class JuryPVForm(forms.ModelForm):
    fichier = forms.FileField(
        label="PV du jury (PDF)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        help_text="Téléchargez le procès-verbal du jury au format PDF ou image.",
        required=False
    )
    observations = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label="Observations",
        required=False
    )

    class Meta:
        model = JuryPV
        fields = ['fichier', 'observations']


class JuryNoteForm(forms.ModelForm):
    note_formation = forms.DecimalField(
        max_digits=5, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '60', 'placeholder': '0-60'}),
        label="Note formation (/60)"
    )
    note_jury = forms.DecimalField(
        max_digits=5, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '40', 'placeholder': '0-40'}),
        label="Note jury (/40)"
    )

    class Meta:
        model = JuryNote
        fields = ['stagiaire', 'note_formation', 'note_jury']

    def __init__(self, *args, **kwargs):
        action = kwargs.pop('action', None)
        super().__init__(*args, **kwargs)
        if action:
            self.fields['stagiaire'].queryset = Stagiaire.objects.filter(
                detailaction__action=action, detailaction__active=True
            ).order_by('nom', 'postnom', 'prenom')
        self.fields['stagiaire'].widget.attrs.update({'class': 'form-select'})
        self.fields['stagiaire'].label = "Stagiaire"


JuryNoteFormSet = forms.inlineformset_factory(
    JuryPV, JuryNote,
    form=JuryNoteForm,
    extra=1,
    can_delete=True,
    fields=['stagiaire', 'note_formation', 'note_jury'],
)
