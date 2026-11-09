from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.db.models import Count, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView, DeleteView
from django.forms import modelformset_factory
from django.shortcuts import render, redirect

from training.models import Filiere, Formation, Module
from progress.models import Formateur, Action, ModuleSubject # Import ModuleSubject
from training.forms import FormationForm, ModuleForm, ModuleFormSet, ModuleSubjectFormSet # Import ModuleSubjectFormSet


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
        queryset = Formation.objects.all().order_by('nom')

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        # Allow Conseiller and Pédagogique to view formations (read-only)
        if user.profile and user.profile.name in ["Conseiller", "Pédagogique"]:
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
    paginate_by = 10
    template_name = "training/formations.html"

    def get_queryset(self):
        # Allow viewing for users; management actions are enforced on create/update/delete views
        queryset = self.get_formation_queryset().select_related("filiere", "filiere__service")

        # --- Filtres et recherche ---
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(nom__icontains=q) |
                Q(description__icontains=q) |
                Q(filiere__nom__icontains=q)
            )

        type_f = self.request.GET.get('type_formation', '').strip()
        if type_f:
            queryset = queryset.filter(type_formation=type_f)

        filiere_id = self.request.GET.get('filiere', '').strip()
        if filiere_id:
            queryset = queryset.filter(filiere_id=filiere_id)

        active = self.request.GET.get('active', '').strip()
        if active == 'active':
            queryset = queryset.filter(active=True)
        elif active == 'inactive':
            queryset = queryset.filter(active=False)

        queryset = queryset.annotate(
            modules_count=Count('modules', distinct=True),
            actions_count=Count('actions', distinct=True)
        )
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = "formations"

        # Utiliser le queryset de base (non paginé) pour les statistiques globales
        all_formations = self.get_queryset().all()
        total = all_formations.count()
        active_count = all_formations.filter(active=True).count()
        
        # Utiliser l'agrégation pour des totaux corrects et performants
        aggregates = all_formations.aggregate(total_modules=Sum('modules_count'), total_actions=Sum('actions_count'))
        total_modules = aggregates.get('total_modules') or 0
        total_actions = aggregates.get('total_actions') or 0

        ctx["hero_stats"] = [
            {'label': 'Total Formations', 'value': total},
            {'label': 'Actives', 'value': active_count},
            {'label': 'Modules', 'value': total_modules},
            {'label': 'Actions', 'value': total_actions},
        ]

        # Construire actions du hero en respectant les permissions
        user = self.request.user
        hero_actions = [
            {'label': 'Voir les formateurs', 'url': reverse_lazy('formateurs'), 'icon': 'bi bi-person-badge', 'class': 'btn-light-secondary'},
        ]
        if user.is_superuser or (getattr(user, 'profile', None) and getattr(user.profile, 'name', None) in ['Manager', 'Chef de filière', 'Chef de service']):
            hero_actions.insert(0, {'label': 'Nouvelle formation', 'url': reverse_lazy('formation_create'), 'icon': 'bi bi-folder-plus'})
        ctx['hero_actions'] = hero_actions
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
        
        # Construire hero_actions en respectant les permissions de gestion
        hero_actions = [
            {'label': 'Retour à la liste', 'url': reverse_lazy('formations'), 'icon': 'bi bi-arrow-left', 'class': 'btn-light-secondary'},
        ]
        user = self.request.user
        if user.is_superuser or (getattr(user, 'profile', None) and getattr(user.profile, 'name', None) in ['Manager', 'Chef de filière', 'Chef de service']):
            hero_actions.append({'label': 'Modifier', 'url': reverse_lazy('formation_update', kwargs={'pk': formation.pk}), 'icon': 'bi bi-pencil'})

        ctx['hero_actions'] = hero_actions

        return ctx


@method_decorator(login_required, name="dispatch")
class FormationCreateUpdateView(FormationPermissionMixin, View): # Vue unifiée pour créer et modifier
    template_name = "training/formation_form.html" # Nouveau template pour le formulaire

    def get(self, request, pk=None):
        self.enforce_manage_permission()
        formation = None
        if pk:
            formation = get_object_or_404(Formation, pk=pk)
            form = FormationForm(instance=formation)
            formset = ModuleFormSet(instance=formation)
            mode = "edit"
            titre = "Modifier une formation"
        else:
            form = FormationForm()
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
            form = FormationForm(request.POST, instance=formation)
            formset = ModuleFormSet(request.POST, instance=formation)
            mode = "edit"
            titre = "Modifier une formation"
        else:
            form = FormationForm(request.POST)
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
            if pk is None:
                return HttpResponseRedirect(reverse_lazy("formation_update", kwargs={"pk": formation.pk}))
            return HttpResponseRedirect(reverse_lazy("formation", kwargs={"pk": formation.pk}))
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

    def dispatch(self, request, *args, **kwargs):
        # Enforce management permission for delete
        self.enforce_manage_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        ctx["has_actions"] = self.object.actions.exists()
        return ctx

    def form_valid(self, form):
        if self.object.actions.exists():
            messages.error(
                self.request,
                "Cette formation ne peut pas être supprimée car elle est liée à une ou plusieurs actions de formation.",
            )
            return HttpResponseRedirect(reverse_lazy("formation", kwargs={"pk": self.object.pk}))

        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "Cette formation ne peut pas être supprimée car elle est encore utilisée par d'autres éléments.",
            )
            return HttpResponseRedirect(reverse_lazy("formation", kwargs={"pk": self.object.pk}))

@method_decorator(login_required, name="dispatch")
class ModuleCreateView(FormationPermissionMixin, View):
    """Vue pour créer un module pour une formation spécifique."""
    template_name = "training/module_form.html"

    def get(self, request, formation_pk=None):
        self.enforce_manage_permission()
        allowed_formations = self.get_formation_queryset()
        formation = None
        if formation_pk is not None:
            formation = get_object_or_404(Formation, pk=formation_pk)
            if not allowed_formations.filter(pk=formation.pk).exists():
                raise PermissionDenied("Vous n'avez pas la permission de gérer cette formation.")
        form = ModuleForm()
        if formation is None:
            form.fields["formation"].queryset = allowed_formations
        else:
            form.fields.pop("formation")
        ctx = {
            "form": form,
            "formation": formation,
            "titre": f"Nouveau module pour {formation.nom}" if formation else "Nouveau module",
            "mode": "new" if formation else "select",
            "link": "modules",
        }
        return render(request, self.template_name, ctx)

    def post(self, request, formation_pk=None):
        self.enforce_manage_permission()
        allowed_formations = self.get_formation_queryset()
        formation = None
        if formation_pk is not None:
            formation = get_object_or_404(Formation, pk=formation_pk)
            if not allowed_formations.filter(pk=formation.pk).exists():
                raise PermissionDenied("Vous n'avez pas la permission de gérer cette formation.")
        form = ModuleForm(request.POST)
        if formation is None:
            form.fields["formation"].queryset = allowed_formations
        else:
            form.fields.pop("formation")
        if form.is_valid():
            module = form.save(commit=False)
            if formation is not None:
                module.formation = formation
            # Si l'ordre n'est pas spécifié, utiliser le prochain ordre disponible
            if not module.ordre:
                max_ordre = Module.objects.filter(formation=module.formation).aggregate(models.Max('ordre'))['ordre__max'] or 0
                module.ordre = max_ordre + 1
            module.save()
            messages.success(request, f"Module '{module.titre}' créé avec succès.")
            if request.POST.get("modal_submit") == "1":
                return redirect("formation_update", pk=module.formation.pk)
            return redirect("formation", pk=module.formation.pk)
        else:
            if request.POST.get("modal_submit") == "1":
                messages.error(request, "Le module n'a pas été enregistré. Vérifiez les champs saisis.")
                return redirect("formation_update", pk=formation.pk)
            ctx = {
                "form": form,
                "formation": formation,
                "titre": f"Nouveau module pour {formation.nom}" if formation else "Nouveau module",
                "mode": "new" if formation else "select",
                "link": "modules",
            }
            return render(request, self.template_name, ctx)
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
        

@method_decorator(login_required, name="dispatch")
class ModuleFormateursView(FormationPermissionMixin, View):
    """Gérer les formateurs d'un module spécifique."""
    template_name = "training/module_formateurs.html"

    def get(self, request, pk):
        self.enforce_manage_permission()
        module = get_object_or_404(Module, pk=pk)

        allowed_formations = self.get_formation_queryset()
        if not allowed_formations.filter(pk=module.formation.pk).exists():
            raise PermissionDenied("Vous n'avez pas la permission de gérer ce module.")

        formateurs_disponibles = Formateur.objects.all().order_by('nom', 'postnom')
        formateurs_selectionnes = module.formateurs.all()

        ctx = {
            "module": module,
            "formation": module.formation,
            "formateurs_disponibles": formateurs_disponibles,
            "formateurs_selectionnes": formateurs_selectionnes,
            "titre": f"Formateurs du module : {module.titre}",
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        self.enforce_manage_permission()
        module = get_object_or_404(Module, pk=pk)

        allowed_formations = self.get_formation_queryset()
        if not allowed_formations.filter(pk=module.formation.pk).exists():
            raise PermissionDenied("Vous n'avez pas la permission de gérer ce module.")

        formateur_ids = request.POST.getlist("formateurs")
        module.formateurs.set(formateur_ids)

        messages.success(request, f"Les formateurs du module '{module.titre}' ont été mis à jour avec succès.")
        return redirect("modules")


@method_decorator(login_required, name="dispatch")
class ModuleListView(FormationPermissionMixin, ListView):
    """Liste de tous les modules avec leurs formateurs, pour gestion globale."""
    model = Module
    template_name = "training/module_list.html"
    context_object_name = "modules"
    paginate_by = 20

    def get_queryset(self):
        queryset = Module.objects.all().select_related("formation", "formation__filiere").prefetch_related("formateurs").order_by("formation__nom", "ordre")
        user = self.request.user
        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            pass  # will apply filters below
        elif user.profile and user.profile.name == "Chef de filière" and user.filiere:
            queryset = queryset.filter(formation__filiere=user.filiere)
        elif user.profile and user.profile.name == "Chef de service" and user.service:
            queryset = queryset.filter(formation__filiere__service=user.service)
        else:
            return Module.objects.none()

        # --- Filtres et recherche ---
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(nom__icontains=q) |
                Q(description__icontains=q) |
                Q(formation__nom__icontains=q) |
                Q(formation__filiere__nom__icontains=q)
            )

        type_f = self.request.GET.get('type_formation', '').strip()
        if type_f:
            # Note: Module doesn't have type_formation, filtering by formation type
            queryset = queryset.filter(formation__type_formation=type_f)

        filiere_id = self.request.GET.get('filiere', '').strip()
        if filiere_id:
            queryset = queryset.filter(formation__filiere_id=filiere_id)

        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Gestion des modules"
        ctx["link"] = "modules"
        # Filtres de recherche
        ctx["query"] = self.request.GET.get('q', '')
        ctx["type_f"] = self.request.GET.get('type_formation', '')
        ctx["filiere_id"] = self.request.GET.get('filiere', '')
        # Ajout des filières pour le filtre
        ctx["filieres"] = Filiere.objects.all()
        user = self.request.user
        can_manage = user.is_superuser or (
            user.profile and user.profile.name in ["Manager", "Chef de filière", "Chef de service"]
        )
        ctx["hero_actions"] = [
            {
                "label": "Ajouter un module",
                "url": reverse_lazy("module_create_select"),
                "icon": "bi bi-plus-lg",
            }
        ] if can_manage else []
        return ctx

@method_decorator(login_required, name="dispatch")
class ModuleUpdateView(FormationPermissionMixin, View):
    template_name = "training/module_form.html"

    def get(self, request, pk):
        self.enforce_manage_permission()
        module = get_object_or_404(Module, pk=pk)
        allowed_formations = self.get_formation_queryset()
        if not allowed_formations.filter(pk=module.formation.pk).exists():
            raise PermissionDenied("Vous n'avez pas la permission de modifier ce module.")
        form = ModuleForm(instance=module)
        form.fields["formation"].queryset = allowed_formations
        ctx = {
            "form": form,
            "formation": module.formation,
            "titre": f"Modifier le module : {module.titre}",
            "mode": "edit",
            "module": module,
            "link": "modules",
            "return_to": request.GET.get("return_to"),
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        self.enforce_manage_permission()
        module = get_object_or_404(Module, pk=pk)
        allowed_formations = self.get_formation_queryset()
        if not allowed_formations.filter(pk=module.formation.pk).exists():
            raise PermissionDenied("Vous n'avez pas la permission de modifier ce module.")
        form = ModuleForm(request.POST, instance=module)
        form.fields["formation"].queryset = allowed_formations
        if form.is_valid():
            module = form.save()
            messages.success(request, f"Module '{module.titre}' mis à jour avec succès.")
            if request.POST.get("return_to") == "formation_update":
                return redirect("formation_update", pk=module.formation.pk)
            return redirect("modules")
        ctx = {
            "form": form,
            "formation": module.formation,
            "titre": f"Modifier le module : {module.titre}",
            "mode": "edit",
            "module": module,
            "link": "modules",
            "return_to": request.POST.get("return_to"),
        }
        return render(request, self.template_name, ctx)

@method_decorator(login_required, name="dispatch")
class ModuleDeleteView(FormationPermissionMixin, DeleteView):
    """Vue pour supprimer un module."""
    model = Module
    template_name = "training/module_confirm_delete.html"
    context_object_name = "module"
    success_url = reverse_lazy("modules")

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(formation__filiere=user.filiere)
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(formation__filiere__service=user.service)
        return queryset.none()

    def get_success_url(self):
        messages.success(self.request, "Module supprimé avec succès.")
        if self.request.POST.get("return_to") == "formation_update":
            return reverse_lazy("formation_update", kwargs={"pk": self.object.formation_id})
        return self.success_url