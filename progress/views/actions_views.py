import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from progress.models import Action, Formateur, ModuleProgress
from training.models import Formation, Module


class ActionPermissionMixin:
    def normalize_formateur_ids(self, formateur_ids):
        return [int(formateur_id) for formateur_id in formateur_ids if str(formateur_id).isdigit()]

    def get_allowed_formations(self):
        user = self.request.user
        queryset = Formation.objects.all().prefetch_related("modules__formateurs")
        
        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(filiere=user.filiere)
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(filiere__service=user.service)
        return Formation.objects.none()

    def get_queryset(self):
        allowed_formations = self.get_allowed_formations()
        if not allowed_formations.exists():
            return Action.objects.none()
        return (
            Action.objects.filter(formation__in=allowed_formations)
            .select_related("formation", "formation__filiere")
            .prefetch_related("formateurs")
            .annotate(stagiaire_total=Count("detailaction", distinct=True), formateur_total=Count("formateurs", distinct=True))
            .order_by("-date_debut", "-id")
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if not self.get_queryset().filter(pk=obj.pk).exists():
            raise PermissionDenied("Vous n'avez pas la permission d'accéder à cette ressource.")
        return obj

    def enforce_manage_permission(self):
        if not self.get_allowed_formations().exists():
            raise PermissionDenied("Vous n'avez pas la permission de gérer les actions.")

    def get_action_status(self, action):
        today = date.today()
        if action.date_fin < today:
            return {"label": "Terminée", "badge": "bg-light-secondary text-dark", "key": "completed"}
        if action.date_debut > today:
            return {"label": "Planifiée", "badge": "bg-light-primary text-primary", "key": "planned"}
        return {"label": "En cours", "badge": "bg-light-success text-success", "key": "ongoing"}

    def build_form_context(self, **kwargs):
        allowed_formations = self.get_allowed_formations()
        all_formateurs = Formateur.objects.filter(active=True).order_by("nom", "postnom")

        formations_data = []
        modules_formateurs_assignment = {} # New dictionary to store module-formateur assignments for the current action

        for formation in allowed_formations:
            modules_data = []
            formateurs_for_formation = set() # Formateurs eligible for any module in this formation
            for module in formation.modules.all():
                module_formateurs = module.formateurs.all()
                for f in module_formateurs:
                    formateurs_for_formation.add(f)
                modules_data.append({
                    "id": module.id,
                    "titre": module.titre,
                    "duree_heures": module.duree_heures,
                    # We need to pass the formateurs assigned to this module (from the Module model itself)
                    "assigned_formateurs_ids": [f.id for f in module_formateurs],
                })

            formations_data.append({
                "id": formation.id,
                "nom": formation.nom,
                "modules": modules_data, # Now includes module-specific formateurs
                "formateurs_ids": [f.id for f in formateurs_for_formation], # These are formateurs eligible for any module in this formation
            })

        context = {
            "formations": allowed_formations,
            "formateurs": all_formateurs,
            "formations_json": formations_data,
            "formateurs_json": list(all_formateurs.values("id", "nom", "postnom", "prenom")),
            "today": date.today(),
            "selected_formateur_ids": [], # This is for Action.formateurs, which we might remove or keep separate
        }

        # If in update mode, populate initial module-formateur assignments for the specific action being edited
        action_object = kwargs.get('object') # Get the action object if available
        if action_object and action_object.pk:
            # On récupère les assignations réelles depuis ModuleProgress pour CETTE action
            progressions = ModuleProgress.objects.filter(action=action_object)
            for prog in progressions:
                if prog.module_id not in modules_formateurs_assignment:
                    modules_formateurs_assignment[prog.module_id] = []
                modules_formateurs_assignment[prog.module_id].append(prog.formateur_id)
            context["modules_formateurs_assignment_json"] = modules_formateurs_assignment
        else:
            context["modules_formateurs_assignment_json"] = {} # Empty for create view

        context.update(kwargs)
        return context

    def _save_module_assignments(self, action, request):
        """Helper to create ModuleProgress records based on selected formateurs per module."""
        all_assigned_formateur_ids = set()

        # 1. On récupère les progressions existantes pour éviter les doublons et la perte de données
        existing_progress = {
            (p.module_id, p.formateur_id): p 
            for p in ModuleProgress.objects.filter(action=action)
        }
        
        new_assignments = set()

        for module in action.formation.modules.all():
            formateur_ids = request.POST.getlist(f"module_formateurs_{module.id}")
            valid_ids = [int(fid) for fid in formateur_ids if str(fid).isdigit()]

            for f_id in valid_ids:
                new_assignments.add((module.id, f_id))
                all_assigned_formateur_ids.add(f_id)
                
                # 2. On ne crée que si ça n'existe pas déjà
                if (module.id, f_id) not in existing_progress:
                    ModuleProgress.objects.create(
                        action=action,
                        module=module,
                        formateur_id=f_id,
                        statut_module='NC'
                    )

        # 3. On supprime les assignations qui ont été décochées dans le formulaire
        for (m_id, f_id), progress_obj in existing_progress.items():
            if (m_id, f_id) not in new_assignments:
                if progress_obj.sessions_progress.exists():
                    messages.error(
                        request, 
                        f"Le formateur {progress_obj.formateur} ne peut pas être retiré du module '{progress_obj.module.titre}' "
                        f"car des séances de formation ont déjà été enregistrées."
                    )
                    all_assigned_formateur_ids.add(f_id) # On garde le formateur dans la liste globale de l'action
                    continue
                progress_obj.delete()

        # Optionnel: Mettre à jour Action.formateurs (M2M) pour le récapitulatif global
        if all_assigned_formateur_ids:
            action.formateurs.set(list(all_assigned_formateur_ids))

    def validate_action_payload(self, date_debut, date_fin, formation_id, formateur_ids):
        errors = []
        allowed_formations = self.get_allowed_formations()

        if not allowed_formations.filter(pk=formation_id).exists():
            errors.append("La formation sélectionnée n'est pas autorisée pour votre périmètre.")
        if date_fin and date_debut and date_fin < date_debut:
            errors.append("La date de fin doit être postérieure ou égale à la date de début.")

        if formation_id:
            try:
                selected_formation = Formation.objects.get(pk=formation_id)
                # This logic is for Action.formateurs, which we are now moving away from for assignment
                # allowed_formateur_ids_for_formation = set(
                #     Module.objects.filter(formation=selected_formation)
                #     .exclude(formateurs__isnull=True)
                #     .values_list("formateurs__id", flat=True)
                # )

                # requested_formateurs_pks = set(self.normalize_formateur_ids(formateur_ids))

                # for pk in requested_formateurs_pks:
                #     if pk not in allowed_formateur_ids_for_formation:
                #         formateur_obj = Formateur.objects.get(pk=pk)
                #         errors.append(
                #             f"Le formateur '{formateur_obj.nom} {formateur_obj.postnom}' ne dispense aucun module de la formation sélectionnée."
                #         )
                pass # No longer validating Action.formateurs directly here
            except Formation.DoesNotExist:
                errors.append("La formation sélectionnée est introuvable.")

        return errors


@method_decorator(login_required, name="dispatch")
class ActionListViews(ActionPermissionMixin, ListView):
    context_object_name = "action_list"
    model = Action
    template_name = "progress/actions.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        page_actions = list(ctx["object_list"])
        all_actions = self.get_queryset()

        for action in page_actions:
            action.status_meta = self.get_action_status(action)

        ctx["object_list"] = page_actions
        ctx["link"] = "actions"
        ctx["stats"] = {
            "total": all_actions.count(),
            "planned": all_actions.filter(date_debut__gt=date.today()).count(),
            "ongoing": all_actions.filter(date_debut__lte=date.today(), date_fin__gte=date.today()).count(),
            "completed": all_actions.filter(date_fin__lt=date.today()).count(),
            "enrolled": all_actions.aggregate(total=Count("detailaction", distinct=True))["total"] or 0,
        }
        return ctx


@method_decorator(login_required, name="dispatch")
class ActionDetailViews(ActionPermissionMixin, DetailView):
    model = Action
    template_name = "progress/action_detail.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("formation", "formation__filiere")
            .prefetch_related(
                "detailaction_set__stagiaire",
                "formateurs",
                "formation__modules__formateurs",
                "formation__modules__seances__formateur",
                "formation__modules__seances__evaluateur",
                "module_progressions",
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        action = ctx["object"]
        inscriptions = action.detailaction_set.select_related("stagiaire").order_by("stagiaire__nom", "stagiaire__postnom")

        # On récupère la liste des modules une seule fois
        modules_list = list(action.formation.modules.all().order_by("ordre"))
        # On récupère toutes les progressions de cette action pour filtrer en mémoire (plus performant)
        all_progressions = list(action.module_progressions.all().select_related('formateur'))

        for module in modules_list:
            module.sessions = list(
                module.seances.select_related("formateur", "evaluateur").order_by("date_debut_reelle", "created_at")
            )
            # On attache les progressions filtrées pour ce module spécifique
            module.module_progressions = [p for p in all_progressions if p.module_id == module.id]
            module.module_progressions.sort(key=lambda x: x.formateur.nom)

        ctx["modules"] = modules_list
        ctx["status_meta"] = self.get_action_status(action)
        ctx["inscriptions"] = inscriptions
        ctx["link"] = "actions"
        ctx["inscription_count"] = inscriptions.count()
        ctx["formateurs_assignes"] = action.formateurs.all().order_by("nom", "postnom")
        return ctx


@method_decorator(login_required, name="dispatch")
class ActionCreateView(ActionPermissionMixin, View):
    def get(self, request):
        self.enforce_manage_permission()
        ctx = self.build_form_context(
            titre="Créer",
            mode="new",
            submitted={},
            selected_formateur_ids=[],
        )
        return render(request, "progress/action.html", ctx)

    def post(self, request):
        self.enforce_manage_permission()

        description = request.POST["description"].strip()
        date_debut = request.POST["date_debut"]
        date_fin = request.POST["date_fin"]
        formation_id = request.POST["formation"]
        # formateur_ids = request.POST.getlist("formateurs") # Removed direct Action.formateurs assignment

        errors = self.validate_action_payload(date_debut, date_fin, formation_id, []) # Pass empty list for formateur_ids
        if errors:
            ctx = self.build_form_context(
                titre="Créer",
                mode="new",
                submitted=request.POST,
                selected_formateur_ids=[], # No longer tracking action-level formateurs
                form_errors=errors,
            )
            return render(request, "progress/action.html", ctx, status=400)

        action = Action(
            description=description,
            date_debut=date_debut,
            date_fin=date_fin,
            formation_id=formation_id,
        )
        action.save()
        # Removed direct Action.formateurs assignment
        # if formateur_ids:
        #     action.formateurs.set(Formateur.objects.filter(pk__in=self.normalize_formateur_ids(formateur_ids)))

        # New: Process module-specific formateur assignments for creation
        self._save_module_assignments(action, request)

        return HttpResponseRedirect(reverse_lazy("actions"))

@method_decorator(login_required, name="dispatch")
class ActionUpdateView(ActionPermissionMixin, UpdateView):
    model = Action
    template_name = "progress/action.html"
    fields = ["description", "date_debut", "date_fin", "formation"]
    success_url = reverse_lazy("actions")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["formation"].queryset = self.get_allowed_formations().select_related("filiere").order_by("nom")
        return form

    def form_valid(self, form):
        # formateur_ids = self.request.POST.getlist("formateurs") # Removed direct Action.formateurs assignment
        errors = self.validate_action_payload(
            form.cleaned_data["date_debut"],
            form.cleaned_data["date_fin"],
            str(form.cleaned_data["formation"].pk),
            [], # Pass empty list for formateur_ids
        )
        if errors:
            for error in errors:
                form.add_error(None, error)
            return self.form_invalid(form)
        
        response = super().form_valid(form) # Saves the Action object
        self._save_module_assignments(self.object, self.request)

        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            self.build_form_context(
                titre="Modifier",
                mode="edit",
                object=self.object, # Pass the object to build_form_context
                selected_formateur_ids=[], # No longer tracking action-level formateurs
            )
        )
        return ctx


@method_decorator(login_required, name="dispatch")
class ActionDeleteView(ActionPermissionMixin, DeleteView):
    model = Action
    template_name = "progress/action_confirm_delete.html"
    success_url = reverse_lazy("actions")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        return ctx