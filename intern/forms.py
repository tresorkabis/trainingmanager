from django import forms
from django_select2.forms import Select2Widget, ModelSelect2TagWidget
from .models import Stagiaire, Categorie, Entreprise

class StagiaireForm(forms.ModelForm):
    categorie = forms.ModelChoiceField(
        queryset=Categorie.objects.filter(titre__in=["dans l'emploi", "sans emploi"]).order_by('titre'),
        label="Catégorie",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'}) # Utilisation de Select2Widget ici aussi
    )
    # Use a CharField with Select2 tagging enabled so users can type a new company name.
    # clean_entreprise will return an Entreprise instance so ModelForm assigns the FK correctly.
    # Use a CharField with a ModelSelect2TagWidget so both existing PKs and free-text names are accepted.
    entreprise = forms.CharField(
        label="Entreprise",
        required=False,
        widget=ModelSelect2TagWidget(model=Entreprise, search_fields=["nom__icontains"], attrs={'data-width': '100%', 'class': 'form-select', 'data-tags': 'true', 'data-minimum-input-length': '0'})
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
            'nom_pere', 'nom_mere', 'niveau_etude', 'photo', 'categorie',
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
            if not isinstance(field.widget, Select2Widget) and not isinstance(field.widget, ModelSelect2TagWidget):
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
        
        # Si la donnée est déjà une instance du modèle, c'est une sélection existante.
        if isinstance(data, Entreprise):
            return data
        
        # ModelSelect2TagWidget envoie l'ID en chaîne pour les sélections existantes
        # et le texte brut pour les nouvelles balises.
        if isinstance(data, str):
            try:
                # C'est un ID d'une entreprise existante
                entreprise_id = int(data)
                return Entreprise.objects.get(pk=entreprise_id)
            except (ValueError, Entreprise.DoesNotExist):
                # C'est un nouveau nom d'entreprise à créer
                entreprise_nom = data.strip()
                if entreprise_nom:
                    entreprise, _ = Entreprise.objects.get_or_create(nom=entreprise_nom)
                    return entreprise
        
        return None
