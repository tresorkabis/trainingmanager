from django import forms
from django_select2.forms import Select2Widget
from .models import Stagiaire, Categorie, Entreprise


class EntrepriseForm(forms.ModelForm):
    class Meta:
        model = Entreprise
        fields = ["nom", "adresse", "telephone", "email", "active"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "adresse": forms.TextInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class StagiaireForm(forms.ModelForm):
    categorie = forms.ModelChoiceField(
        queryset=Categorie.objects.filter(titre__in=["dans l'emploi", "sans emploi"]).order_by('titre'),
        label="Catégorie",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select select2'}) # Utilisation de Select2Widget ici aussi
    )
    # Plain text input accepts company names with spaces; clean_entreprise maps
    # an existing ID/name to its model instance or creates a new company.
    entreprise = forms.CharField(
        label="Entreprise",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': 'entreprises-list',
            'autocomplete': 'organization',
        }),
    )

    class Meta:
        model = Stagiaire
        fields = [
            'nom', 'postnom', 'prenom', 'adresse', 'sexe', 'telephone', 'email',
            'nationalite', 'type_piece', 'numero_piece',
            'niveau_etude', 'photo', 'categorie',
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
            'nationalite': forms.TextInput(attrs={'class': 'form-control'}),
            'type_piece': forms.Select(attrs={'class': 'form-select'}),
            'numero_piece': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau_etude': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control'}),
            'anciennete_emploi': forms.NumberInput(attrs={'class': 'form-control'}),
            'anciennete_entreprise': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.entreprise_id:
            self.initial['entreprise'] = self.instance.entreprise.nom
        # Assurez-vous que tous les champs ont la classe form-control ou form-select
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, Select2Widget):
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})
                elif isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs.update({'class': 'form-check-input'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})

    def clean_entreprise(self):
        data = self.cleaned_data.get('entreprise')
        
        if not data:
            return None
        
        entreprise_nom = data.strip()
        if not entreprise_nom:
            return None

        # Accept an existing company ID for compatibility with previously rendered forms.
        try:
            entreprise_id = int(entreprise_nom)
        except ValueError:
            entreprise_id = None
        if entreprise_id is not None:
            entreprise = Entreprise.objects.filter(pk=entreprise_id).first()
            if entreprise:
                return entreprise

        entreprise = Entreprise.objects.filter(nom__iexact=entreprise_nom).first()
        if entreprise:
            return entreprise
        return Entreprise.objects.create(nom=entreprise_nom)
