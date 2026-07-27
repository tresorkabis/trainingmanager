from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count # Import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, DeleteView # Import UpdateView and DeleteView

from training.models import Service, Filiere, Formation


class ServicePermissionMixin:
    def enforce_manage_permission(self):
        user = self.request.user
        # Exemple: Seuls les superutilisateurs et managers peuvent gérer les services
        if not (user.is_superuser or (user.profile and user.profile.name == "Manager")):
            raise PermissionDenied("Vous n'avez pas la permission de gérer les services.")

@method_decorator(login_required, name="dispatch")
class ServiceListView(ServicePermissionMixin, ListView):
    context_object_name = "service_list"
    template_name = "training/services.html"
    paginate_by = 4

    def get_queryset(self):
        self.enforce_manage_permission() # Vérifier la permission avant de construire le queryset
        queryset = Service.objects.all().order_by('nom')
        
        # Annoter chaque service avec le nombre de filières et de formations
        queryset = queryset.annotate(
            filieres_count=Count('filieres', distinct=True), # CHANGÉ 'filiere' à 'filieres'
            metiers_count=Count('filieres__formations', distinct=True)
        )
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "services"
        
        # Calcul des statistiques globales
        all_services = self.get_queryset()
        total = all_services.count()
        active = all_services.filter(active=True).count()
        total_filieres = all_services.aggregate(total_filieres=Count('filieres', distinct=True))['total_filieres'] or 0
        
        ctx["hero_stats"] = [
            {'label': 'Total Services', 'value': total},
            {'label': 'Actifs', 'value': active},
            {'label': 'Inactifs', 'value': total - active},
            {'label': 'Filières', 'value': total_filieres},
        ]

        ctx["hero_actions"] = [
            {'label': 'Nouveau service', 'url': reverse_lazy('service_create'), 'icon': 'bi bi-plus-circle'},
        ]
        return ctx

@method_decorator(login_required, name="dispatch")
class ServiceDetailView(ServicePermissionMixin, DetailView):
    model = Service
    template_name = "training/service_detail.html" # Nouveau template pour le détail
    context_object_name = "service"

    def get_queryset(self):
        return super().get_queryset().prefetch_related('filieres__formations')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        service = ctx['service']
        
        ctx['filieres_associees'] = service.filieres.all().prefetch_related('formations').order_by('nom')
        ctx['titre'] = "Détail du service"
        
        # Stats pour le Hero
        ctx["hero_stats"] = [
            {'label': 'Filières', 'value': ctx['filieres_associees'].count()},
            {'label': 'Statut', 'value': "Actif" if service.active else "Inactif"},
            {'label': 'Date création', 'value': service.created_at.strftime("%d/%m/%Y")},
            {'label': 'ID', 'value': f"#SRV-{service.pk}"},
        ]
        
        ctx["hero_actions"] = [
            {'label': 'Retour à la liste', 'url': reverse_lazy('services'), 'icon': 'bi bi-arrow-left', 'class': 'btn-light-secondary'},
            {'label': 'Modifier', 'url': reverse_lazy('service_update', kwargs={'pk': service.pk}), 'icon': 'bi bi-pencil'},
        ]
        return ctx

@method_decorator(login_required, name="dispatch")
class ServiceCreateUpdateView(ServicePermissionMixin, View): # Nouvelle vue pour créer/modifier
    template_name = "training/service_form.html" # Nouveau template

    def get(self, request, pk=None):
        self.enforce_manage_permission()
        service = None
        if pk:
            service = get_object_or_404(Service, pk=pk)
        
        ctx = {
            "titre": "Modifier un service" if pk else "Créer un service",
            "mode": "edit" if pk else "new",
            "object": service,
            "submitted": {}, # Pour gérer les erreurs de formulaire
        }
        return render(request, self.template_name, ctx)
    
    def post(self, request, pk=None):
        self.enforce_manage_permission()
        service = None
        if pk:
            service = get_object_or_404(Service, pk=pk)

        nom = request.POST.get('nom', '').strip()
        active = request.POST.get('active') == 'on' # Gérer le champ active

        errors = []
        if not nom:
            errors.append("Le nom du service est requis.")
        
        # Validation d'unicité du nom
        if Service.objects.filter(nom=nom).exclude(pk=pk).exists():
            errors.append(f"Un service avec le nom '{nom}' existe déjà.")

        if errors:
            ctx = {
                "titre": "Modifier un service" if pk else "Créer un service",
                "mode": "edit" if pk else "new",
                "object": service, # Si c'est une modification, l'objet existe
                "submitted": request.POST, # Repopuler le formulaire avec les données soumises
                "form_errors": errors,
            }
            return render(request, self.template_name, ctx, status=400)

        if service: # Mode édition
            service.nom = nom
            service.active = active
            service.save()
        else: # Mode création
            service = Service.objects.create(
                nom=nom,
                active=active,
            )
        
        return HttpResponseRedirect(reverse_lazy("services"))

@method_decorator(login_required, name="dispatch")
class ServiceDeleteView(ServicePermissionMixin, DeleteView):
    model = Service
    template_name = "training/service_confirm_delete.html" # Nouveau template pour la confirmation de suppression
    success_url = reverse_lazy("services")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        return ctx
