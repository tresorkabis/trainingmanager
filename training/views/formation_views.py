from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView, DeleteView

from training.models import Filiere, Formation, Module
from progress.models import Formateur, Action, ModuleSubject # Import ModuleSubject
from training.forms import MetierForm, ModuleFormSet, ModuleSubjectFormSet # Import ModuleSubjectFormSet


class FormationPermissionMixin:
    def get_allowed_filieres(self):
        user = self.request.user
        queryset = Filiere.objects.all()

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(pk=user.filiere.pk)
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(service=user.service)
        return Filiere.objects.none()

    def get_formation_queryset(self):
        user = self.request.user
        queryset = Formation.objects.all()

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(filiere=user.filiere)
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(filiere__service=user.service)
        return Formation.objects.none()

    def enforce_manage_permission(self):
        user = self.request.user
        if not (user.is_superuser or (user.profile and user.profile.name in ["Manager", "Chef de filière", "Chef de service"])):
            raise PermissionDenied("Vous n'avez pas la permission de gérer les formations.")


@method_decorator(login_required, name="dispatch")
class FormationListView(FormationPermissionMixin, ListView):
    # Expose as 'formation_list' for templates that expect that name
    context_object_name = "formation_list"
    paginate_by = 4
    template_name = "training/formations.html"

    def get_queryset(self):
        self.enforce_manage_permission()
        queryset = self.get_formation_queryset().select_related("filiere", "filiere__service")

        queryset = queryset.annotate(
            modules_count=Count('modules', distinct=True),
            actions_count=Count('actions', distinct=True)
        )
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = "formations"

        all_formations = self.get_queryset()
        total = all_formations.count()
        active = all_formations.filter(active=True).count()
        total_modules = all_formations.aggregate(total_modules=Count('modules', distinct=True))['total_modules'] or 0
        total_actions = all_formations.aggregate(total_actions=Count('actions', distinct=True))['total_actions'] or 0

        ctx['stats'] = {
            'total': total,
            'active': active,
            'inactive': all_formations.filter(active=False).count(),
            'total_modules': total_modules,
            'total_actions': total_actions,
        }

        ctx["hero_stats"] = [
            {'label': 'Total Formations', 'value': total},
            {'label': 'Actives', 'value': active},
            {'label': 'Modules', 'value': total_modules},
            {'label': 'Actions', 'value': total_actions},
        ]

        ctx["hero_actions"] = [
            {'label': 'Nouvelle formation', 'url': reverse_lazy('formation_create'), 'icon': 'bi bi-folder-plus'},
            {'label': 'Voir les formateurs', 'url': reverse_lazy('formateurs'), 'icon': 'bi bi-person-badge', 'class': 'btn-light-secondary'},
        ]
        return ctx


@method_decorator(login_required, name="dispatch")
class FormationDetailView(FormationPermissionMixin, DetailView):
    model = Formation
    template_name = "training/formation.html"
    context_object_name = "object" # Utilise 'object' comme nom de contexte par défaut

    def get_queryset(self):
        return self.get_formation_queryset().select_related("filiere", "filiere__service").prefetch_related("modules__formateurs", "actions") # Prefetch actions

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        formation = self.get_object()
        
        ctx["filieres"] = self.get_allowed_filieres()
        ctx["formateurs"] = Formateur.objects.all()
        ctx["titre"] = "Voir"
        ctx["mode"] = "view"
        ctx["link"] = "formations"
        ctx["actions"] = formation.actions.all()

        # Hero Context
        ctx["hero_stats"] = [
            {'label': 'Modules', 'value': formation.modules.count()},
            {'label': 'Durée', 'value': f"{formation.duree_heures}h"},
            {'label': 'Coût', 'value': f"{formation.cout:,.0f} USD"},
            {'label': 'Sessions', 'value': formation.actions.count()},
        ]
        
        ctx["hero_actions"] = [
            {'label': 'Retour à la liste', 'url': reverse_lazy('formations'), 'icon': 'bi bi-arrow-left', 'class': 'btn-light-secondary'},
            {'label': 'Modifier', 'url': reverse_lazy('formation_update', kwargs={'pk': formation.pk}), 'icon': 'bi bi-pencil'},
        ]

        return ctx


@method_decorator(login_required, name="dispatch")
class FormationCreateUpdateView(FormationPermissionMixin, View): # Vue unifiée pour créer et modifier
    template_name = "training/formation_form.html" # Nouveau template pour le formulaire

    def get(self, request, pk=None):
        self.enforce_manage_permission()
        formation = None
        if pk:
            formation = get_object_or_404(Formation, pk=pk)
            form = MetierForm(instance=formation)
            formset = ModuleFormSet(instance=formation)
            mode = "edit"
            titre = "Modifier une formation"
        else:
            form = MetierForm()
            formset = ModuleFormSet()
            mode = "new"
            titre = "Créer une formation"

        ctx = {
            "form": form,
            "formset": formset,
            "filieres": self.get_allowed_filieres(),
            "formateurs": Formateur.objects.all(), # Peut être utile pour le JS du formset
            "titre": titre,
            "mode": mode,
            "object": formation, # Passe l'objet métier s'il existe
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        self.enforce_manage_permission()
        formation = None
        if pk:
            formation = get_object_or_404(Formation, pk=pk)
            form = MetierForm(request.POST, instance=formation)
            formset = ModuleFormSet(request.POST, instance=formation)
            mode = "edit"
            titre = "Modifier une formation"
        else:
            form = MetierForm(request.POST)
            formset = ModuleFormSet(request.POST)
            mode = "new"
            titre = "Créer une formation"

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                formation = form.save(commit=False)

                # Validation de la filière
                filiere_id = form.cleaned_data["filiere"].pk
                if not self.get_allowed_filieres().filter(pk=filiere_id).exists():
                    messages.error(request, "Vous n'avez pas la permission de rattacher cette formation à cette filière.")
                    return self.form_invalid(request, form, formset, formation, mode, titre)

                formation.save()
                formset.instance = formation # Assurez-vous que le formset est lié à l'instance du métier
                formset.save()

                # Recalculer duree_heures après la sauvegarde des modules
                total_duree_heures = sum(module.duree_heures for module in formation.modules.all())
                if formation.duree_heures != total_duree_heures:
                    formation.duree_heures = total_duree_heures
                    formation.save(update_fields=['duree_heures'])

            messages.success(request, f"La formation '{formation.nom}' a été {'mise à jour' if pk else 'créée'} avec succès.")
            return HttpResponseRedirect(reverse_lazy("formation", kwargs={'pk': formation.pk}))
        else:
            return self.form_invalid(request, form, formset, formation, mode, titre)

    def form_invalid(self, request, form, formset, formation, mode, titre):
        ctx = {
            "form": form,
            "formset": formset,
            "filieres": self.get_allowed_filieres(),
            "formateurs": Formateur.objects.all(),
            "titre": titre,
            "mode": mode,
            "object": formation,
            "form_errors": form.errors,
            "formset_errors": formset.errors, # Passer les erreurs du formset
        }
        return render(request, self.template_name, ctx, status=400)


@method_decorator(login_required, name="dispatch")
class ModuleSubjectManageView(FormationPermissionMixin, View):
    template_name = "training/module_subjects_form.html"

    def get(self, request, pk):
        self.enforce_manage_permission()
        module = get_object_or_404(Module, pk=pk)
        formset = ModuleSubjectFormSet(instance=module)
        
        ctx = {
            "module": module,
            "formset": formset,
            "titre": f"Sujets du module : {module.titre}",
            "hero_actions": [
                {'label': 'Retour à la formation', 'url': reverse_lazy('formation', kwargs={'pk': module.formation.pk}), 'icon': 'bi bi-arrow-left', 'class': 'btn-light-secondary'},
            ]
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        self.enforce_manage_permission()
        module = get_object_or_404(Module, pk=pk)
        formset = ModuleSubjectFormSet(request.POST, instance=module)
        
        if formset.is_valid():
            with transaction.atomic():
                formset.save()
                
                # Calcul et mise à jour de la durée du module
                hours_per_session = float(request.POST.get('hours-per-session', 2))
                total_sessions = sum(s.nombre_seances for s in module.subjects.all())
                module.duree_heures = int(total_sessions * hours_per_session)
                module.save()
                
                # Mise à jour de la durée totale de la formation
                formation = module.formation
                total_formation_hours = sum(m.duree_heures for m in formation.modules.all())
                if formation.duree_heures != total_formation_hours:
                    formation.duree_heures = total_formation_hours
                    formation.save(update_fields=['duree_heures'])
                
            messages.success(request, f"Les sujets du module '{module.titre}' ont été mis à jour (Durée : {module.duree_heures}h).")
            return HttpResponseRedirect(reverse_lazy("formation", kwargs={'pk': module.formation.pk}))
        
        ctx = {
            "module": module,
            "formset": formset,
            "titre": f"Sujets du module : {module.titre}",
            "formset_errors": formset.errors,
        }
        return render(request, self.template_name, ctx, status=400)


@method_decorator(login_required, name="dispatch")
class FormationDeleteView(FormationPermissionMixin, DeleteView):
    model = Formation
    template_name = "training/formation_confirm_delete.html"
    success_url = reverse_lazy("formations")
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        return ctx

# La vue ModuleFormateursUpdateView n'est plus nécessaire car la gestion des formateurs
# se fait via le formset dans FormationCreateUpdateView.
# @method_decorator(login_required, name="dispatch")
# class ModuleFormateursUpdateView(FormationPermissionMixin, View):
#     """Vue pour mettre à jour uniquement les formateurs d'un module spécifique."""
#     def post(self, request, pk):
#         self.enforce_manage_permission()
#         module = get_object_or_404(Module, pk=pk)
        
#         allowed_formations = self.get_formation_queryset()
#         if not allowed_formations.filter(pk=module.formation.pk).exists():
#             raise PermissionDenied("Vous n'avez pas la permission de modifier ce module.")

#         formateur_ids = [fid for fid in request.POST.getlist('formateur_ids') if fid]
        
#         module.formateurs.set(formateur_ids)
        
#         messages.success(request, f"Les formateurs du module '{module.titre}' ont été mis à jour avec succès.")
        
#         return HttpResponseRedirect(reverse_lazy("formation", kwargs={'pk': module.formation.pk}))