from django import forms
from django_select2.forms import Select2Widget
from .models import Stagiaire, Categorie, Filiere, Entreprise

class StagiaireForm(forms.ModelForm):
    categorie = forms.ModelChoiceField(
        queryset=Categorie.objects.all().order_by('titre'),
        label="Catégorie",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )
    filiere = forms.ModelChoiceField(
        queryset=Filiere.objects.all().order_by('nom'),
        label="Filière",
        required=False,
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )
    entreprise = forms.ModelChoiceField(
        queryset=Entreprise.objects.all().order_by('nom'),
        label="Entreprise",
        required=False,
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )
    date_naissance = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date de naissance",
        required=False
    )

    class Meta:
        model = Stagiaire
        fields = [
            'nom', 'postnom', 'prenom', 'adresse', 'sexe', 'telephone', 'email',
            'date_naissance', 'lieu_naissance', 'nationalite', 'type_piece', 'numero_piece',
            'nom_pere', 'nom_mere', 'niveau_etude', 'photo', 'categorie', 'filiere',
            'entreprise', 'fonction', 'anciennete_emploi', 'anciennete_entreprise'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'postnom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-select'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'nationalite': forms.TextInput(attrs={'class': 'form-control'}),
            'type_piece': forms.Select(attrs={'class': 'form-select'}),
            'numero_piece': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_pere': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_mere': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau_etude': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control'}),
            'anciennete_emploi': forms.NumberInput(attrs={'class': 'form-control'}),
            'anciennete_entreprise': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Assurez-vous que tous les champs ont la classe form-control ou form-select
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, Select2Widget):
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})
                elif isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs.update({'class': 'form-check-input'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})
