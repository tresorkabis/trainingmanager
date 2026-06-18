from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count # Import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView, DeleteView # Ajout de DeleteView

from progress.models import Formateur
# from training.models import Module, Action # Pas besoin d'importer ici, les related_name suffisent

class FormateurPermissionMixin:
    def enforce_manage_permission(self):
        user = self.request.user
        # Exemple: Seuls les superutilisateurs et managers peuvent gérer les formateurs
        if not (user.is_superuser or (user.profile and user.profile.name == "Manager")):
            raise PermissionDenied("Vous n'avez pas la permission de gérer les formateurs.")

class FormateurListView(FormateurPermissionMixin, ListView):
    context_object_name = "formateur_list"
    template_name = "progress/formateurs.html"
    paginate_by = 10 # Ajout de la pagination

    def get_queryset(self):
        self.enforce_manage_permission() # Vérifier la permission avant de construire le queryset
        queryset = Formateur.objects.all().order_by('nom', 'postnom')
        
        # Annoter chaque formateur avec le nombre de modules et d'actions
        queryset = queryset.annotate(
            modules_count=Count('modules_dispenses', distinct=True),
            actions_count=Count('actions', distinct=True)
        )
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "formateurs"
        
        # Calcul des statistiques globales
        all_formateurs = self.get_queryset()
        total = all_formateurs.count()
        active = all_formateurs.filter(active=True).count()
        inactive = total - active

        ctx['stats'] = {
            'total': total,
            'active': active,
            'inactive': inactive,
        }

        ctx["hero_stats"] = [
            {'label': 'Total Formateurs', 'value': total},
            {'label': 'Actifs', 'value': active},
            {'label': 'Inactifs', 'value': inactive},
        ]

        ctx["hero_actions"] = [
            {'label': 'Nouveau formateur', 'url': reverse_lazy('formateur_create'), 'icon': 'bi bi-person-plus'},
        ]
        return ctx

@method_decorator(login_required, name="dispatch")
class FormateurDetailView(FormateurPermissionMixin, DetailView): # Nouvelle vue de détail
    model = Formateur
    template_name = "progress/formateur_detail.html" # Nouveau template
    context_object_name = "formateur"

    def get_queryset(self):
        # Précharger les modules dispensés et les actions associées
        return super().get_queryset().prefetch_related("modules_dispenses__formation", "actions__formation")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        formateur = ctx['formateur']
        
        ctx["modules_dispenses"] = formateur.modules_dispenses.all().select_related("formation").order_by("formation__nom", "ordre")
        ctx["actions_assignees"] = formateur.actions.all().select_related("formation").order_by("-date_debut")
        ctx["performances"] = formateur.performances.all().select_related("action", "module").order_by("-action__date_debut")
        ctx['titre'] = "Détail du formateur"

        ctx["hero_stats"] = [
            {'label': 'Modules', 'value': ctx["modules_dispenses"].count()},
            {'label': 'Actions', 'value': ctx["actions_assignees"].count()},
            {'label': 'Spécialité', 'value': formateur.specialite or "N/A"},
        ]

        ctx["hero_actions"] = [
            {'label': 'Retour', 'url': reverse_lazy('formateurs'), 'icon': 'bi bi-arrow-left', 'class': 'btn-light-secondary'},
            {'label': 'Modifier', 'url': reverse_lazy('formateur_update', kwargs={'pk': formateur.pk}), 'icon': 'bi bi-pencil'},
        ]
        return ctx

@method_decorator(login_required, name="dispatch")
class FormateurCreateUpdateView(FormateurPermissionMixin, View):
    template_name = "progress/formateur_form.html"

    def get(self, request, pk=None):
        self.enforce_manage_permission()
        formateur = None
        if pk:
            formateur = get_object_or_404(Formateur, pk=pk)
        
        ctx = {
            "titre": "Modifier" if pk else "Créer",
            "mode": "edit" if pk else "new",
            "object": formateur,
            "submitted": {}, # Pour gérer les erreurs de formulaire
        }
        return render(request, self.template_name, ctx)
    
    def post(self, request, pk=None):
        self.enforce_manage_permission()
        formateur = None
        if pk:
            formateur = get_object_or_404(Formateur, pk=pk)

        matricule = request.POST.get('matricule', '').strip()
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip() # Récupérer le prénom
        postnom = request.POST.get('postnom', '').strip()
        adresse = request.POST.get('adresse', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        email = request.POST.get('email', '').strip()
        active = request.POST.get('active') == 'on' # Gérer le champ active
        specialite = request.POST.get('specialite', '').strip() # Récupérer la spécialité

        errors = []
        if not matricule:
            errors.append("Le matricule est requis.")
        if not nom:
            errors.append("Le nom est requis.")
        if not postnom:
            errors.append("Le postnom est requis.")
        if not email:
            errors.append("L'email est requis.")
        
        # Validation d'unicité du matricule
        if Formateur.objects.filter(matricule=matricule).exclude(pk=pk).exists():
            errors.append(f"Un formateur avec le matricule '{matricule}' existe déjà.")
        # Validation d'unicité de l'email
        if Formateur.objects.filter(email=email).exclude(pk=pk).exists():
            errors.append(f"Un formateur avec l'email '{email}' existe déjà.")

        if errors:
            ctx = {
                "titre": "Modifier" if pk else "Créer",
                "mode": "edit" if pk else "new",
                "object": formateur, # Si c'est une modification, l'objet existe
                "submitted": request.POST, # Repopuler le formulaire avec les données soumises
                "form_errors": errors,
            }
            return render(request, self.template_name, ctx, status=400)

        if formateur: # Mode édition
            formateur.matricule = matricule
            formateur.nom = nom
            formateur.prenom = prenom # Assigner le prénom
            formateur.postnom = postnom
            formateur.adresse = adresse
            formateur.telephone = telephone
            formateur.email = email
            formateur.active = active # Mettre à jour le statut actif
            formateur.specialite = specialite # Mettre à jour la spécialité
            formateur.save()
        else: # Mode création
            formateur = Formateur.objects.create(
                matricule=matricule,
                nom=nom,
                prenom=prenom, # Assigner le prénom
                postnom=postnom,
                adresse=adresse,
                telephone=telephone,
                email=email,
                active=active, # Définir le statut actif
                specialite=specialite, # Assignation de la spécialité
            )
        
        return HttpResponseRedirect(reverse_lazy("formateurs"))

@method_decorator(login_required, name="dispatch")
class FormateurDeleteView(FormateurPermissionMixin, DeleteView):
    model = Formateur
    template_name = "progress/formateur_confirm_delete.html" # Nouveau template pour la confirmation de suppression
    success_url = reverse_lazy("formateurs")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        return ctx
