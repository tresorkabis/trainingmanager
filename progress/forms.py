from django import forms
from django.core.exceptions import ValidationError
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
        # Assurez-vous que tous les champs ont la classe form-control ou form-select
        for field_name, field in self.fields.items():
            # Les champs stagiaire, action, date_paiement, motif, mode_paiement, montant ont déjà leurs classes définies
            # Soit via le widget directement, soit via Meta.widgets
            pass # Plus besoin de boucle générique ici car tout est géré explicitement

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
        # Filtrer dynamiquement les modules basés sur la formation de l'action sélectionnée
        if 'action' in self.data:
            from .models import Action
            try:
                action_id = int(self.data.get('action'))
                action_obj = Action.objects.get(pk=action_id)
                self.fields['module'].queryset = Module.objects.filter(
                    formation=action_obj.formation
                ).order_by('ordre')
            except (ValueError, TypeError, Action.DoesNotExist):
                pass # Fallback to default queryset if selection is invalid

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
