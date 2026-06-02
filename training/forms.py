from django import forms
from django_select2.forms import Select2Widget
from .models import Metier, Module, Filiere
from progress.models import Formateur

class MetierForm(forms.ModelForm):
    filiere = forms.ModelChoiceField(
        queryset=Filiere.objects.all().order_by('nom'),
        label="Filière",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )

    class Meta:
        model = Metier
        fields = ["nom", "duree", "filiere", "cout", "frais_participation", "frais_jury", "frais_materiels"]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'duree': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'filiere' est géré par ModelChoiceField ci-dessus
            'cout': forms.NumberInput(attrs={'class': 'form-control'}),
            'frais_participation': forms.NumberInput(attrs={'class': 'form-control'}),
            'frais_jury': forms.NumberInput(attrs={'class': 'form-control'}),
            'frais_materiels': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Assurez-vous que tous les champs ont la classe form-control ou form-select
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, Select2Widget): # Select2Widget a déjà ses classes
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})

# Formulaire pour un module individuel
class ModuleForm(forms.ModelForm):
    formateurs = forms.ModelMultipleChoiceField(
        queryset=Formateur.objects.all().order_by('nom', 'postnom'),
        label="Formateurs",
        required=False,
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )

    class Meta:
        model = Module
        fields = ["titre", "description", "duree_heures", "formateurs", "ordre"]
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'duree_heures': forms.NumberInput(attrs={'class': 'form-control'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'formateurs' est géré par ModelMultipleChoiceField ci-dessus
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, Select2Widget):
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})
