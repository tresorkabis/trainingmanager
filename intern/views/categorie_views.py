from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count # Import Count for statistics
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy # Import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, DeleteView # Import UpdateView and DeleteView

from intern.models import Categorie, Stagiaire # Import Stagiaire for statistics


class CategoriePermissionMixin:
    def enforce_manage_permission(self):
        user = self.request.user
        # Exemple: Seuls les superutilisateurs et managers peuvent gérer les catégories
        if not (user.is_superuser or (user.profile and user.profile.name == "Manager")):
            raise PermissionDenied("Vous n'avez pas la permission de gérer les catégories.")

@method_decorator(login_required, name="dispatch")
class CategorieListView(CategoriePermissionMixin, ListView):
    context_object_name = "categorie_list"
    template_name = "intern/categories.html"
    paginate_by = 10 # Ajout de la pagination

    def get_queryset(self):
        self.enforce_manage_permission() # Vérifier la permission avant de construire le queryset
        queryset = Categorie.objects.all().order_by('titre')
        
        # Annoter chaque catégorie avec le nombre de stagiaires
        queryset = queryset.annotate(
            stagiaires_count=Count('stagiaire', distinct=True) # 'stagiaire' est le related_name par défaut pour ForeignKey de Stagiaire vers Categorie
        )
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "categories"
        
        # Calcul des statistiques globales
        all_categories = self.get_queryset() # Utiliser le queryset annoté
        total = all_categories.count()
        active = all_categories.filter(active=True).count()
        total_stagiaires = all_categories.aggregate(total_stagiaires=Count('stagiaire', distinct=True))['total_stagiaires'] or 0

        ctx['stats'] = {
            'total': total,
            'active': active,
            'inactive': total - active,
            'total_stagiaires': total_stagiaires,
        }

        ctx['hero_stats'] = [
            {'label': 'Total Catégories', 'value': total},
            {'label': 'Actives', 'value': active},
            {'label': 'Inactives', 'value': total - active},
            {'label': 'Total Stagiaires', 'value': total_stagiaires},
        ]
        
        ctx['hero_actions'] = [
            {'label': 'Nouvelle catégorie', 'url': reverse_lazy('categorie_create'), 'icon': 'bi bi-bookmark-plus'},
        ]
        return ctx

@method_decorator(login_required, name="dispatch")
class CategorieDetailView(CategoriePermissionMixin, DetailView):
    model = Categorie
    template_name = "intern/categorie_detail.html" # Nouveau template pour le détail
    context_object_name = "categorie"

    def get_queryset(self):
        return super().get_queryset().prefetch_related('stagiaire_set') # Précharger les stagiaires

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        categorie = ctx['categorie']
        
        ctx['stagiaires_associes'] = categorie.stagiaire_set.all().order_by('nom', 'postnom')
        ctx['titre'] = "Détail de la catégorie"
        
        # Stats pour le Hero
        ctx["hero_stats"] = [
            {'label': 'Stagiaires', 'value': ctx['stagiaires_associes'].count()},
            {'label': 'Statut', 'value': "Active" if categorie.active else "Inactive"},
            {'label': 'Date création', 'value': categorie.created_at.strftime("%d/%m/%Y")},
            {'label': 'ID', 'value': f"#CAT-{categorie.pk}"},
        ]
        
        ctx["hero_actions"] = [
            {'label': 'Retour à la liste', 'url': reverse_lazy('categories'), 'icon': 'bi bi-arrow-left', 'class': 'btn-light-secondary'},
            {'label': 'Modifier', 'url': reverse_lazy('categorie_update', kwargs={'pk': categorie.pk}), 'icon': 'bi bi-pencil'},
        ]
        return ctx

@method_decorator(login_required, name="dispatch")
class CategorieCreateUpdateView(CategoriePermissionMixin, View): # Nouvelle vue pour créer/modifier
    template_name = "intern/categorie_form.html" # Nouveau template

    def get(self, request, pk=None):
        self.enforce_manage_permission()
        categorie = None
        if pk:
            categorie = get_object_or_404(Categorie, pk=pk)
        
        ctx = {
            "titre": "Modifier une catégorie" if pk else "Créer une catégorie",
            "mode": "edit" if pk else "new",
            "object": categorie,
            "submitted": {}, # Pour gérer les erreurs de formulaire
        }
        return render(request, self.template_name, ctx)
    
    def post(self, request, pk=None):
        self.enforce_manage_permission()
        categorie = None
        if pk:
            categorie = get_object_or_404(Categorie, pk=pk)

        titre = request.POST.get('titre', '').strip()
        active = request.POST.get('active') == 'on' # Gérer le champ active

        errors = []
        if not titre:
            errors.append("Le titre de la catégorie est requis.")
        
        # Validation d'unicité du titre
        if Categorie.objects.filter(titre=titre).exclude(pk=pk).exists():
            errors.append(f"Une catégorie avec le titre '{titre}' existe déjà.")

        if errors:
            ctx = {
                "titre": "Modifier une catégorie" if pk else "Créer une catégorie",
                "mode": "edit" if pk else "new",
                "object": categorie, # Si c'est une modification, l'objet existe
                "submitted": request.POST, # Repopuler le formulaire avec les données soumises
                "form_errors": errors,
            }
            return render(request, self.template_name, ctx, status=400)

        if categorie: # Mode édition
            categorie.titre = titre
            categorie.active = active
            categorie.save()
        else: # Mode création
            categorie = Categorie.objects.create(
                titre=titre,
                active=active,
            )
        
        return HttpResponseRedirect(reverse_lazy("categories"))

@method_decorator(login_required, name="dispatch")
class CategorieDeleteView(CategoriePermissionMixin, DeleteView):
    model = Categorie
    template_name = "intern/categorie_confirm_delete.html" # Nouveau template pour la confirmation de suppression
    success_url = reverse_lazy("categories")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        return ctx