from django import forms
from .models import Paiement, Stagiaire, Action

class PaiementForm(forms.ModelForm):
    # Permet de filtrer les stagiaires et actions si nécessaire, ou de les afficher tous
    stagiaire = forms.ModelChoiceField(queryset=Stagiaire.objects.all(), label="Stagiaire")
    action = forms.ModelChoiceField(queryset=Action.objects.all(), required=False, label="Action de formation")
    date_paiement = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Date du paiement")

    class Meta:
        model = Paiement
        fields = ['stagiaire', 'action', 'montant', 'date_paiement', 'motif', 'mode_paiement', 'reference']
        labels = {
            'montant': 'Montant',
            'motif': 'Motif',
            'mode_paiement': 'Mode de paiement',
            'reference': 'Référence',
        }
        widgets = {
            'motif': forms.Textarea(attrs={'rows': 3}),
        }