from django import forms
from django_select2.forms import Select2Widget # Importez Select2Widget
from .models import Paiement, Stagiaire, Action

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

    class Meta:
        model = Paiement
        fields = ['stagiaire', 'action', 'montant', 'date_paiement', 'motif', 'mode_paiement']
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
