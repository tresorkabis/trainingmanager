from django import forms
from django_select2.forms import Select2Widget, ModelSelect2TagWidget
from .models import Stagiaire, Categorie, Filiere, Entreprise

class StagiaireForm(forms.ModelForm):
    categorie = forms.ModelChoiceField(
        queryset=Categorie.objects.all().order_by('titre'),
        label="Catégorie",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    filiere = forms.ModelChoiceField(
        queryset=Filiere.objects.all().order_by('nom'),
        label="Filière",
        required=False,
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
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
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, Select2Widget):
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})
                elif isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs.update({'class': 'form-check-input'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})

    def clean_entreprise(self):
        entreprise_data = self.cleaned_data.get('entreprise')

        # Normalize: Select2 may return a list/tuple, or a JSON array string like '["SNEL"]'.
        if isinstance(entreprise_data, (list, tuple)):
            entreprise_data = entreprise_data[0] if entreprise_data else None

        if isinstance(entreprise_data, str):
            s = entreprise_data.strip()
            # Normalize common array-like representations, e.g. "['SNEL']", '["SNEL"]', or plain 'SNEL'
            # If it's a Python-like list with single quotes, json.loads will fail — try to strip brackets/quotes manually.
            if s.startswith('[') and s.endswith(']'):
                # Remove outer brackets
                inner = s[1:-1].strip()
                # If inner looks like a quoted string, strip quotes
                if (inner.startswith("'") and inner.endswith("'")) or (inner.startswith('"') and inner.endswith('"')):
                    entreprise_data = inner[1:-1].strip()
                else:
                    # try json.loads for well-formed JSON
                    try:
                        import json
                        parsed = json.loads(s)
                        if isinstance(parsed, (list, tuple)) and parsed:
                            entreprise_data = parsed[0]
                    except Exception:
                        # fallback: split by comma and take first token
                        entreprise_data = inner.split(',')[0].strip().strip('"\'')
            else:
                # not bracketed, keep trimmed string
                entreprise_data = s

        # Si entreprise_data est déjà une instance d'Entreprise (cas d'une sélection existante)
        if isinstance(entreprise_data, Entreprise):
            return entreprise_data

        # Si entreprise_data est None ou vide, et que le champ n'est pas requis, on retourne None
        if not entreprise_data and not self.fields['entreprise'].required:
            return None

        # Si c'est une chaîne, cela peut être un nouveau nom ou un ID existant sous forme de chaîne
        if isinstance(entreprise_data, str):
            # Tente de convertir en int pour voir si c'est un ID existant
            try:
                entreprise_id = int(entreprise_data)
                # Si c'est un ID, récupère l'entreprise existante
                return Entreprise.objects.get(pk=entreprise_id)
            except (ValueError, Entreprise.DoesNotExist):
                # Si ce n'est pas un ID numérique ou si l'entreprise n'existe pas,
                # c'est un nouveau nom d'entreprise à créer.
                new_entreprise_name = entreprise_data.strip()
                if new_entreprise_name:
                    entreprise, created = Entreprise.objects.get_or_create(
                        nom=new_entreprise_name,
                        defaults={'active': True} # Définir d'autres valeurs par défaut si nécessaire
                    )
                    return entreprise
                else:
                    raise forms.ValidationError("Le nom de l'entreprise ne peut pas être vide.")

        # If we reach here, return None to avoid storing unexpected types
        return None
