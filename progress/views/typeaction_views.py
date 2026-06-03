from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count # Import Count for statistics
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy # Import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, DeleteView # Import UpdateView and DeleteView

from progress.models import TypeAction, Action # Import Action model


class TypeActionPermissionMixin:
    def enforce_manage_permission(self):
        user = self.request.user
        # Exemple: Seuls les superutilisateurs et managers peuvent gérer les types d'action
        if not (user.is_superuser or (user.profile and user.profile.name == "Manager")):
            raise PermissionDenied("Vous n'avez pas la permission de gérer les types d'action.")

@method_decorator(login_required, name="dispatch")
class TypeActionListView(TypeActionPermissionMixin, ListView):
    context_object_name = "typeAction_list"
    template_name = "progress/typeactions.html"
    paginate_by = 10 # Ajout de la pagination

    def get_queryset(self):
        self.enforce_manage_permission() # Vérifier la permission avant de construire le queryset
        return (
            TypeAction.objects.all()
            .annotate(actions_count=Count("actions_liees", distinct=True))
            .order_by("code")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "typeactions"
        
        # Calcul des statistiques globales
        all_typeactions = self.get_queryset() # Utiliser le queryset
        ctx['stats'] = {
            'total': all_typeactions.count(),
            'active': all_typeactions.filter(active=True).count(),
            'inactive': all_typeactions.filter(active=False).count(),
            'actions_total': all_typeactions.aggregate(total=Count("actions_liees", distinct=True))["total"],
        }
        return ctx

@method_decorator(login_required, name="dispatch")
class TypeActionDetailView(TypeActionPermissionMixin, DetailView):
    model = TypeAction
    template_name = "progress/typeaction_detail.html" # Nouveau template pour le détail
    context_object_name = "typeaction"

    def get_queryset(self):
        return super().get_queryset().prefetch_related('actions_liees') # Précharger les actions liées

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        typeaction = ctx['typeaction']

        ctx['actions_associees'] = typeaction.actions_liees.all().select_related("formation", "formation__filiere").order_by("-date_debut") # Récupérer les actions associées
        ctx['titre'] = "Détail du type d'action"
        ctx['link'] = "typeactions" # Ajout de la variable link pour le menu latéral
        return ctx

@method_decorator(login_required, name="dispatch")
class TypeActionCreateUpdateView(TypeActionPermissionMixin, View): # Nouvelle vue pour créer/modifier
    template_name = "progress/typeaction_form.html" # Nouveau template

    def get(self, request, pk=None):
        self.enforce_manage_permission()
        typeaction = None
        if pk:
            typeaction = get_object_or_404(TypeAction, pk=pk)
        
        ctx = {
            "titre": "Modifier" if pk else "Créer",
            "mode": "edit" if pk else "new",
            "object": typeaction,
            "submitted": {}, # Pour gérer les erreurs de formulaire
            "link": "typeactions", # Ajout de la variable link pour le menu latéral
        }
        return render(request, self.template_name, ctx)
    
    def post(self, request, pk=None):
        self.enforce_manage_permission()
        typeaction = None
        if pk:
            typeaction = get_object_or_404(TypeAction, pk=pk)

        code = request.POST.get('code', '').strip()
        libelle = request.POST.get('libelle', '').strip()
        active = request.POST.get('active') == 'on' # Gérer le champ active

        errors = []
        if not code:
            errors.append("Le code est requis.")
        if not libelle:
            errors.append("Le libellé est requis.")
        
        # Validation d'unicité du code
        if TypeAction.objects.filter(code=code).exclude(pk=pk).exists():
            errors.append(f"Un type d'action avec le code '{code}' existe déjà.")
        # Validation d'unicité du libellé
        if TypeAction.objects.filter(libelle=libelle).exclude(pk=pk).exists():
            errors.append(f"Un type d'action avec le libellé '{libelle}' existe déjà.")

        if errors:
            ctx = {
                "titre": "Modifier" if pk else "Créer",
                "mode": "edit" if pk else "new",
                "object": typeaction, # Si c'est une modification, l'objet existe
                "submitted": request.POST, # Repopuler le formulaire avec les données soumises
                "form_errors": errors,
                "link": "typeactions", # Ajout de la variable link pour le menu latéral
            }
            return render(request, self.template_name, ctx, status=400)

        if typeaction: # Mode édition
            typeaction.code = code
            typeaction.libelle = libelle
            typeaction.active = active
            typeaction.save()
        else: # Mode création
            typeaction = TypeAction.objects.create(
                code=code,
                libelle=libelle,
                active=active,
            )
        
        return HttpResponseRedirect(reverse_lazy("typeactions"))

@method_decorator(login_required, name="dispatch")
class TypeActionDeleteView(TypeActionPermissionMixin, DeleteView):
    model = TypeAction
    template_name = "progress/typeaction_confirm_delete.html" # Nouveau template pour la confirmation de suppression
    success_url = reverse_lazy("typeactions")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        ctx['link'] = "typeactions" # Ajout de la variable link pour le menu latéral
        return ctx
