from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django_select2.forms import Select2Widget

from .models import User, Profile
from training.models import Filiere, Service


class CustomAuthenticationForm(AuthenticationForm):
    """Formulaire d'authentification avec un message d'erreur en français."""
    error_messages = {
        'invalid_login': "Identifiants invalides",
        'inactive': "Ce compte est inactif.",
    }

class CustomUserCreationForm(UserCreationForm):
    profile = forms.ModelChoiceField(
        queryset=Profile.objects.all().order_by('name'),
        label="Profil",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )
    filiere = forms.ModelChoiceField(
        queryset=Filiere.objects.all().order_by('nom'),
        label="Filière",
        required=False,
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )
    service = forms.ModelChoiceField(
        queryset=Service.objects.all().order_by('nom'),
        label="Service",
        required=False,
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'profile', 'filiere', 'service')
        field_classes = {'username': forms.CharField, 'email': forms.EmailField} # Assurez-vous que email est EmailField

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Appliquer la classe 'form-control' aux champs de texte
        for field_name in ['username', 'email', 'first_name', 'last_name']:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
        
        # Les champs password sont gérés par UserCreationForm.Meta et n'ont pas besoin de form-control ici
        # Les champs Select2 ont déjà leurs classes définies dans leur widget


class CustomUserChangeForm(UserChangeForm):
    profile = forms.ModelChoiceField(
        queryset=Profile.objects.all().order_by('name'),
        label="Profil",
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )
    filiere = forms.ModelChoiceField(
        queryset=Filiere.objects.all().order_by('nom'),
        label="Filière",
        required=False,
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )
    service = forms.ModelChoiceField(
        queryset=Service.objects.all().order_by('nom'),
        label="Service",
        required=False,
        widget=Select2Widget(attrs={'data-width': '100%', 'class': 'form-select'})
    )

    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'profile', 'filiere', 'service')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Appliquer la classe 'form-control' aux champs de texte
        for field_name in ['username', 'email', 'first_name', 'last_name']:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
        
        # Retirer les champs de mot de passe car ils sont gérés séparément
        if 'password' in self.fields:
            del self.fields['password']
        if 'password2' in self.fields:
            del self.fields['password2']
