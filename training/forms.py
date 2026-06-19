from django import forms
from django.forms import inlineformset_factory
from django_select2.forms import Select2Widget

from .models import Formation, Module, Filiere
from progress.models import Formateur, ModuleSubject

class MetierForm(forms.ModelForm):
    filiere = forms.ModelChoiceField(
        queryset=Filiere.objects.all().order_by('nom'),
        label="Filière",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )

    class Meta:
        model = Formation
        fields = ["nom", "duree", "type_formation", "filiere", "cout", "frais_participation", "frais_jury", "frais_materiels"]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'duree': forms.NumberInput(attrs={'class': 'form-control'}),
            'type_formation': forms.Select(choices=Formation.TYPE_CHOICES, attrs={'class': 'form-select'}),
            'cout': forms.NumberInput(attrs={'class': 'form-control'}),
            'frais_participation': forms.NumberInput(attrs={'class': 'form-control'}),
            'frais_jury': forms.NumberInput(attrs={'class': 'form-control'}),
            'frais_materiels': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, Select2Widget):
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})

class ModuleForm(forms.ModelForm):
    formateurs = forms.ModelMultipleChoiceField(
        queryset=Formateur.objects.all().order_by('nom', 'postnom'),
        label="Formateur(s)",
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, Select2Widget):
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})

ModuleFormSet = inlineformset_factory(
    Formation,
    Module,
    form=ModuleForm,
    extra=1,
    can_delete=True,
    fields=["titre", "description", "duree_heures", "formateurs", "ordre"]
)

class ModuleSubjectForm(forms.ModelForm):
    class Meta:
        model = ModuleSubject
        fields = ["titre", "nombre_seances", "ordre", "description"]
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_seances': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

ModuleSubjectFormSet = inlineformset_factory(
    Module,
    ModuleSubject,
    form=ModuleSubjectForm,
    extra=0,
    can_delete=True
)
