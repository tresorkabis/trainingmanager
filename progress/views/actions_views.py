from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied # Import pour gérer les permissions

from progress.models import Action
from training.models import Formation # Importation de Formation pour le filtrage

# Mixin pour la gestion des permissions
class ActionPermissionMixin:
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset() # Commence avec le queryset de base de la vue (e.g., self.model.objects.all())

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        elif user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(formation__filiere=user.filiere)
        elif user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(formation__filiere__service=user.service)
        
        return Action.objects.none() # Par défaut, aucune donnée si aucun rôle spécifique ne correspond

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        # Vérifie si l'objet récupéré est dans le queryset filtré par les permissions
        if not self.get_queryset().filter(pk=obj.pk).exists():
            raise PermissionDenied("Vous n'avez pas la permission d'accéder à cette ressource.")
        return obj

@method_decorator(login_required, name='dispatch')
class ActionListViews(ActionPermissionMixin, ListView):
    context_object_name = "action_list"
    model = Action # <-- Décommenté pour définir le modèle de base
    template_name = "progress/actions.html"

    def get_queryset(self):
        # Le mixin ActionPermissionMixin.get_queryset sera appelé,
        # et il appellera super().get_queryset() qui résoudra correctement
        # le queryset de base grâce à 'model = Action' défini ici.
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "actions"
        return ctx

@method_decorator(login_required, name='dispatch')
class ActionDetailViews(ActionPermissionMixin, DetailView):
    model = Action
    template_name = "progress/action_detail.html"

@method_decorator(login_required, name='dispatch')
class ActionCreateView(ActionPermissionMixin, View): # Utilisation de View pour un contrôle manuel du formulaire
    def get(self, request):
        user = request.user
        formations_queryset = Formation.objects.all()

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            pass
        elif user.profile and user.profile.name == "Chef de filière" and user.filiere:
            formations_queryset = formations_queryset.filter(filiere=user.filiere)
        elif user.profile and user.profile.name == "Chef de service" and user.service:
            formations_queryset = formations_queryset.filter(filiere__service=user.service)
        else:
            formations_queryset = Formation.objects.none()

        ctx = {
            "formations": formations_queryset,
            "titre": "Créer",
            "mode": "new"
        }
        return render(request, 'progress/action.html', ctx)
    
    def post(self, request):
        description = request.POST['description']
        date_debut = request.POST['date_debut']
        date_fin = request.POST['date_fin']
        formation_id = request.POST['formation']
        
        action = Action(
            description = description,
            date_debut = date_debut,
            date_fin = date_fin,
            formation_id = formation_id,
        )
        action.save()

        return HttpResponseRedirect(reverse_lazy("actions"))

@method_decorator(login_required, name='dispatch')
class ActionUpdateView(ActionPermissionMixin, UpdateView):
    model = Action
    template_name = "progress/action.html"
    fields = ['description', 'date_debut', 'date_fin', 'formation']
    success_url = reverse_lazy("actions")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titre'] = "Modifier"
        ctx['mode'] = "edit"
        user = self.request.user
        formations_queryset = Formation.objects.all()

        # Filtrer les formations disponibles pour la modification d'actions
        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            pass
        elif user.profile and user.profile.name == "Chef de filière" and user.filiere:
            formations_queryset = formations_queryset.filter(filiere=user.filiere)
        elif user.profile and user.profile.name == "Chef de service" and user.service:
            formations_queryset = formations_queryset.filter(filiere__service=user.service)
        else:
            formations_queryset = Formation.objects.none()
        
        ctx['formations'] = formations_queryset
        return ctx

@method_decorator(login_required, name='dispatch')
class ActionDeleteView(ActionPermissionMixin, DeleteView):
    model = Action
    template_name = "progress/action_confirm_delete.html" # Nous allons créer ce template
    success_url = reverse_lazy("actions")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titre'] = "Supprimer"
        return ctx