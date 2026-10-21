from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View, TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count

from users.models import User, Profile
from users.forms import CustomUserCreationForm, CustomUserChangeForm
from intern.models import Categorie, Stagiaire

@method_decorator(login_required, name='dispatch')
class UserListView(ListView):
    model = User
    template_name = 'users/users.html'
    context_object_name = 'user_list'
    paginate_by = 10

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("profile", "filiere", "service")
            .order_by("username")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'users' # Pour activer le lien dans le menu latéral
        context['titre'] = 'Liste des utilisateurs'
        # Utiliser le queryset de base (non paginé) pour les statistiques globales
        users_qs = self.get_queryset().all()
        context['hero_actions'] = [
            {
                'label': 'Créer un utilisateur',
                'url': reverse_lazy('user_create'),
                'icon': 'bi bi-person-plus',
            }
        ]
        context['hero_stats'] = [
            {'label': 'Total', 'value': users_qs.count()},
            {'label': 'Avec Profil', 'value': users_qs.exclude(profile__isnull=True).count()},
            {'label': 'Avec Filière', 'value': users_qs.exclude(filiere__isnull=True).count()},
            {'label': 'Avec Service', 'value': users_qs.exclude(service__isnull=True).count()},
        ]
        return context

@method_decorator(login_required, name='dispatch')
class UserCreateView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    
    def get_success_url(self):
        return reverse_lazy('users') # Rediriger vers la liste des utilisateurs après création

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'users'
        context['titre'] = 'Créer un utilisateur'
        context['subtitle'] = 'Créer un nouvel utilisateur.'
        users_qs = User.objects.all()
        context['hero_actions'] = [
            {
                'label': 'Retour à la liste',
                'url': reverse_lazy('users'),
                'icon': 'bi bi-arrow-left',
            }
        ]
        context['hero_stats'] = [
            {'label': 'Total', 'value': users_qs.count()},
            {'label': 'Avec Profil', 'value': users_qs.exclude(profile__isnull=True).count()},
            {'label': 'Avec Filière', 'value': users_qs.exclude(filiere__isnull=True).count()},
            {'label': 'Avec Service', 'value': users_qs.exclude(service__isnull=True).count()},
        ]
        return context

@method_decorator(login_required, name='dispatch')
class UserDetailView(DetailView):
    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'user_object' # Renommé pour éviter conflit avec request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'users'
        context['titre'] = 'Détail de l\'utilisateur'
        user_object = context['user_object']
        context['hero_actions'] = [
            {
                'label': 'Retour à la liste',
                'url': reverse_lazy('users'),
                'icon': 'bi bi-arrow-left',
            }
        ]
        context['hero_stats'] = [
            {'label': 'Profil', 'value': user_object.profile or '—'},
            {'label': 'Filière', 'value': user_object.filiere or '—'},
            {'label': 'Service', 'value': user_object.service or '—'},
        ]
        return context

@method_decorator(login_required, name='dispatch')
class UserUpdateView(UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'

    def get_success_url(self):
        return reverse_lazy('users') # Rediriger vers la liste des utilisateurs après modification

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'users'
        context['titre'] = 'Modifier un utilisateur'
        context['subtitle'] = 'Modifier un utilisateur existant.'
        user_object = self.object
        context['hero_actions'] = [
            {
                'label': 'Retour à la liste',
                'url': reverse_lazy('users'),
                'icon': 'bi bi-arrow-left',
            }
        ]
        context['hero_stats'] = [
            {'label': 'Profil', 'value': user_object.profile or '—'},
            {'label': 'Filière', 'value': user_object.filiere or '—'},
            {'label': 'Service', 'value': user_object.service or '—'},
        ]
        return context

@method_decorator(login_required, name='dispatch')
class UserDeleteView(DeleteView):
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users')
    context_object_name = 'user_object' # Renommé pour éviter conflit avec request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'users'
        context['titre'] = 'Supprimer un utilisateur'
        return context


@method_decorator(login_required, name='dispatch')
class UserResetProfileView(View):
    """
    Réinitialise le profil d'un utilisateur (supprime l'association profile).
    Utilisation : formulaire POST sur {% url 'user_reset_profile' user_object.pk %}
    """
    model = User

    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)
        user.profile = None
        user.save()
        messages.success(request, 'Le profil a été réinitialisé avec succès.')
        return redirect('users')


@method_decorator(login_required, name='dispatch')
class SettingsView(UserPassesTestMixin, TemplateView):
    """
    Page dédiée Réglages (superutilisateurs uniquement).
    Affiche les boutons d'action de réinitialisation : profils et catégories.
    """
    template_name = 'users/settings.html'

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = 'Réglages'
        context['link'] = 'settings'
        # Utilisateurs
        context['total_users'] = User.objects.count()
        context['users_with_profile'] = User.objects.exclude(profile__isnull=True).count()
        context['users_without_profile'] = User.objects.filter(profile__isnull=True).count()
        # Catégories
        context['total_categories'] = Categorie.objects.count()
        context['active_categories'] = Categorie.objects.filter(active=True).count()
        context['inactive_categories'] = Categorie.objects.filter(active=False).count()
        # Stagiaires
        context['total_stagiaires'] = Stagiaire.objects.count()
        context['stagiaires_with_categorie'] = Stagiaire.objects.exclude(categorie__isnull=True).count()
        return context


@method_decorator(login_required, name='dispatch')
class ProfileListView(UserPassesTestMixin, ListView):
    """
    Liste des profils (superutilisateurs uniquement).
    """
    model = Profile
    template_name = 'users/profile_list.html'
    context_object_name = 'profile_list'
    ordering = ['name']

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = 'Liste des profils'
        context['link'] = 'profiles'
        context['total_profiles'] = Profile.objects.count()
        context['profiles_in_use'] = Profile.objects.filter(user__isnull=False).distinct().count()
        context['profiles_unused'] = Profile.objects.filter(user__isnull=True).distinct().count()
        return context


@method_decorator(login_required, name='dispatch')
class UserResetAllProfilesView(UserPassesTestMixin, View):
    """
    Réinitialise les profils de tous les utilisateurs (met profile=None).
    Utilisation : formulaire POST sur {% url 'user_reset_all_profiles' %}
    """
    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        count = User.objects.exclude(profile__isnull=True).update(profile=None)
        messages.success(
            request,
            f'{count} profil(s) ont été réinitialisé(s).'
        )
        return redirect('settings')


@method_decorator(login_required, name='dispatch')
class CategoryResetView(UserPassesTestMixin, View):
    """
    Réinitialise les catégories (désactive toutes les catégories).
    Utilisation : formulaire POST sur {% url 'category_reset' %}
    """
    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        count = Categorie.objects.filter(active=True).update(active=False)
        messages.success(
            request,
            f'{count} catégorie(s) ont été désactivée(s).'
        )
        return redirect('settings')
