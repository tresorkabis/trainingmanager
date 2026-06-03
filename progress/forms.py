from django import forms
from django_select2.forms import Select2Widget # Importez Select2Widget
from .models import Paiement, Stagiaire, Action, FormateurPerformance, Formateur # Import FormateurPerformance et Formateur
from training.models import Module # Import Module

class PaiementForm(forms.ModelForm):
    # Permet de filtrer les stagiaires et actions si nécessaire, ou de les afficher tous
    stagiaire = forms.ModelChoiceField(
        queryset=Stagiaire.objects.all().order_by('nom', 'postnom', 'prenom'), # Ordonner pour une meilleure UX
        label="Stagiaire",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'}) # Ajout des classes pour Select2
    )
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

class FormateurPerformanceForm(forms.ModelForm):
    formateur = forms.ModelChoiceField(
        queryset=Formateur.objects.all().order_by('nom', 'postnom'),
        label="Formateur",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )
    action = forms.ModelChoiceField(
        queryset=Action.objects.all().order_by('description'),
        label="Action de formation",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )
    module = forms.ModelChoiceField(
        queryset=Module.objects.all().order_by('formation__nom', 'ordre'),
        label="Module",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )
    evaluateur = forms.ModelChoiceField(
        queryset=forms.User.objects.all().order_by('first_name', 'last_name'), # Assurez-vous que User est importé
        label="Évaluateur",
        required=False,
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
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
    date_evaluation = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date d'évaluation",
        required=False
    )

    class Meta:
        model = FormateurPerformance
        fields = [
            'formateur', 'action', 'module', 'date_debut_reelle', 'date_fin_reelle',
            'heures_effectuees', 'date_evaluation', 'evaluateur', 'note_pedagogique',
            'note_contenu', 'note_organisation', 'commentaires'
        ]
        widgets = {
            'heures_effectuees': forms.NumberInput(attrs={'class': 'form-control'}),
            'note_pedagogique': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '5'}),
            'note_contenu': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '5'}),
            'note_organisation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '5'}),
            'commentaires': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, Select2Widget):
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})
                elif isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs.update({'class': 'form-check-input'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})