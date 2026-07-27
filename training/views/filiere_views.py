from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count # Import Count for statistics
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy # Import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, DeleteView # Import UpdateView and DeleteView

from training.models import Filiere, Service, Formation


class FilierePermissionMixin:
    def get_filiere_queryset(self):
        user = self.request.user
        queryset = Filiere.objects.all()

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(pk=user.filiere.pk)
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(service=user.service)
        return Filiere.objects.none()

    def get_allowed_services(self):
        user = self.request.user
        queryset = Service.objects.all()

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(pk=user.service.pk)
        return Service.objects.none()

    def can_manage_filieres(self):
        user = self.request.user
        return user.is_superuser or (user.profile and user.profile.name == "Manager")

    def enforce_manage_permission(self): # Renommé pour être plus générique
        if not self.can_manage_filieres():
            raise PermissionDenied("Vous n'avez pas la permission de gérer les filières.")


@method_decorator(login_required, name="dispatch")
class FiliereListView(FilierePermissionMixin, ListView):
    context_object_name = "filiere_list"
    paginate_by = 10 # Ajout de la pagination
    template_name = "training/filieres.html"

    def get_queryset(self):
        queryset = self.get_filiere_queryset().select_related("service")
        
        # Annoter chaque filière avec le nombre de formations
        queryset = queryset.annotate(
            metiers_count=Count('formations', distinct=True)
        )
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = "filieres"
        ctx["can_manage"] = self.can_manage_filieres()
        
        # Calcul des statistiques globales
        all_filieres = self.get_queryset()
        total = all_filieres.count()
        active = all_filieres.filter(active=True).count()
        total_metiers = all_filieres.aggregate(total_metiers=Count('formations', distinct=True))['total_metiers'] or 0
        
        ctx["hero_stats"] = [
            {'label': 'Total Filières', 'value': total},
            {'label': 'Actives', 'value': active},
            {'label': 'Inactives', 'value': total - active},
            {'label': 'Formations', 'value': total_metiers},
        ]

        if self.can_manage_filieres():
            ctx["hero_actions"] = [
                {'label': 'Nouvelle filière', 'url': reverse_lazy('filiere_create'), 'icon': 'bi bi-plus-circle'},
            ]
        else:
            ctx["hero_actions"] = []
        return ctx


@method_decorator(login_required, name="dispatch")
class FiliereDetailView(FilierePermissionMixin, DetailView):
    model = Filiere
    template_name = "training/filiere_detail.html" # Nouveau template pour le détail
    context_object_name = "filiere"

    def get_queryset(self):
        return self.get_filiere_queryset().select_related("service").prefetch_related("formations")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        filiere = ctx['filiere']
        
        ctx['metiers_associees'] = filiere.formations.all().order_by('nom')
        ctx['titre'] = "Détail de la filière"
        ctx["can_manage"] = self.can_manage_filieres()

        # Stats pour le Hero
        metiers_count = ctx['metiers_associees'].count()
        ctx["hero_stats"] = [
            {'label': 'Formations', 'value': metiers_count},
            {'label': 'Statut', 'value': "Active" if filiere.active else "Inactive"},
            {'label': 'Service', 'value': filiere.service.nom if filiere.service else "N/A"},
            {'label': 'ID', 'value': f"#FIL-{filiere.pk}"},
        ]
        
        ctx["hero_actions"] = [
            {'label': 'Retour à la liste', 'url': reverse_lazy('filieres'), 'icon': 'bi bi-arrow-left', 'class': 'btn-light-secondary'},
        ]
        if ctx["can_manage"]:
            ctx["hero_actions"].append(
                {'label': 'Modifier', 'url': reverse_lazy('filiere_update', kwargs={'pk': filiere.pk}), 'icon': 'bi bi-pencil'}
            )
        return ctx


@method_decorator(login_required, name="dispatch")
class FiliereCreateUpdateView(FilierePermissionMixin, View): # Nouvelle vue pour créer/modifier
    template_name = "training/filiere_form.html" # Nouveau template

    def get(self, request, pk=None):
        self.enforce_manage_permission()
        filiere = None
        if pk:
            filiere = get_object_or_404(Filiere, pk=pk)
        
        ctx = {
            "services": self.get_allowed_services(),
            "titre": "Modifier une filière" if pk else "Créer une filière",
            "mode": "edit" if pk else "new",
            "object": filiere,
            "submitted": {}, # Pour gérer les erreurs de formulaire
        }
        return render(request, self.template_name, ctx)
    
    def post(self, request, pk=None):
        self.enforce_manage_permission()
        filiere = None
        if pk:
            filiere = get_object_or_404(Filiere, pk=pk)

        nom = request.POST.get('nom', '').strip()
        service_id = request.POST.get('service', '').strip()
        active = request.POST.get('active') == 'on' # Gérer le champ active

        errors = []
        if not nom:
            errors.append("Le nom de la filière est requis.")
        if not service_id:
            errors.append("Le service est requis.")
        
        # Validation d'unicité du nom
        if Filiere.objects.filter(nom=nom).exclude(pk=pk).exists():
            errors.append(f"Une filière avec le nom '{nom}' existe déjà.")
        
        # Validation du service
        if not self.get_allowed_services().filter(pk=service_id).exists():
            errors.append("Le service sélectionné n'est pas autorisé pour votre périmètre.")

        if errors:
            ctx = {
                "services": self.get_allowed_services(),
                "titre": "Modifier une filière" if pk else "Créer une filière",
                "mode": "edit" if pk else "new",
                "object": filiere, # Si c'est une modification, l'objet existe
                "submitted": request.POST, # Repopuler le formulaire avec les données soumises
                "form_errors": errors,
            }
            return render(request, self.template_name, ctx, status=400)

        if filiere: # Mode édition
            filiere.nom = nom
            filiere.service_id = service_id
            filiere.active = active
            filiere.save()
        else: # Mode création
            filiere = Filiere.objects.create(
                nom=nom,
                service_id=service_id,
                active=active,
            )
        
        return HttpResponseRedirect(reverse_lazy("filieres"))

@method_decorator(login_required, name="dispatch")
class FiliereDeleteView(FilierePermissionMixin, DeleteView):
    model = Filiere
    template_name = "training/filiere_confirm_delete.html" # Nouveau template pour la confirmation de suppression
    success_url = reverse_lazy("filieres")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        return ctx
