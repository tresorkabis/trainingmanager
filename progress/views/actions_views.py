import json # Import the json module
from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from progress.models import Action, Formateur
from training.models import Metier, Module # Changé Formation à Metier


class ActionPermissionMixin:
    def normalize_formateur_ids(self, formateur_ids):
        return [int(formateur_id) for formateur_id in formateur_ids if str(formateur_id).isdigit()]

    def get_allowed_metiers(self): # Changé get_allowed_formations à get_allowed_metiers
        user = self.request.user
        queryset = Metier.objects.all().prefetch_related('modules__formateurs') # Changé Formation à Metier, et related_name de Module
        
        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(filiere=user.filiere)
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(filiere__service=user.service)
        return Metier.objects.none() # Changé Formation à Metier

    def get_queryset(self):
        allowed_metiers = self.get_allowed_metiers() # Changé allowed_formations à allowed_metiers
        if not allowed_metiers.exists():
            return Action.objects.none()
        return (
            Action.objects.filter(metier__in=allowed_metiers) # Changé formation__in à metier__in
            .select_related("metier", "metier__filiere") # Changé formation à metier
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
        if not self.get_allowed_metiers().exists(): # Changé get_allowed_formations à get_allowed_metiers
            raise PermissionDenied("Vous n'avez pas la permission de gérer les actions.")

    def get_action_status(self, action):
        today = date.today()
        if action.date_fin < today:
            return {"label": "Terminée", "badge": "bg-light-secondary text-dark", "key": "completed"}
        if action.date_debut > today:
            return {"label": "Planifiée", "badge": "bg-light-primary text-primary", "key": "planned"}
        return {"label": "En cours", "badge": "bg-light-success text-success", "key": "ongoing"}

    def build_form_context(self, **kwargs):
        allowed_metiers = self.get_allowed_metiers() # Changé allowed_formations à allowed_metiers
        all_formateurs = Formateur.objects.filter(active=True).order_by("nom", "postnom")

        # Prepare metiers data for JavaScript
        metiers_data = [] # Changé formations_data à metiers_data
        for metier in allowed_metiers: # Changé formation in allowed_formations à metier in allowed_metiers
            modules_data = []
            # Get unique formateurs for this metier's modules
            formateurs_for_metier = set() # Changé formateurs_for_formation à formateurs_for_metier
            for module in metier.modules.all(): # Changé formation.modules.all() à metier.modules.all()
                module_formateurs = module.formateurs.all()
                for f in module_formateurs:
                    formateurs_for_metier.add(f)
                modules_data.append({
                    'id': module.id,
                    'titre': module.titre,
                    'duree_heures': module.duree_heures,
                    'formateur_id': module_formateurs[0].id if module_formateurs.exists() else None,
                    'formateur_name': str(module_formateurs[0]) if module_formateurs.exists() else 'Non assigné',
                })
            
            metiers_data.append({ # Changé formations_data à metiers_data
                'id': metier.id,
                'nom': metier.nom,
                'modules': modules_data,
                'formateurs_ids': [f.id for f in formateurs_for_metier], # Changé formateurs_for_formation à formateurs_for_metier
            })

        context = {
            "metiers": allowed_metiers, # Changé formations à metiers
            "formateurs": all_formateurs,
            "metiers_json": json.dumps(metiers_data), # Changé formations_json à metiers_json
            "formateurs_json": json.dumps(list(all_formateurs.values('id', 'nom', 'postnom'))),
            "today": date.today(),
            "selected_formateur_ids": [],
        }
        context.update(kwargs)
        return context

    def validate_action_payload(self, date_debut, date_fin, metier_id, formateur_ids): # Changé formation_id à metier_id
        errors = []
        allowed_metiers = self.get_allowed_metiers() # Changé allowed_formations à allowed_metiers

        if not allowed_metiers.filter(pk=metier_id).exists(): # Changé formation_id à metier_id
            errors.append("Le métier sélectionné n'est pas autorisé pour votre périmètre.") # Changé formation à métier
        if date_fin and date_debut and date_fin < date_debut:
            errors.append("La date de fin doit être postérieure ou égale à la date de début.")
        
        # --- Nouvelle logique de validation des formateurs ---
        if metier_id: # Changé formation_id à metier_id
            try:
                selected_metier = Metier.objects.get(pk=metier_id) # Changé Formation à Metier, formation_id à metier_id
                # Get formateurs assigned to modules of this specific metier
                allowed_formateur_ids_for_metier = set( # Changé allowed_formateur_ids_for_formation à allowed_formateur_ids_for_metier
                    Module.objects.filter(metier=selected_metier) # Changé formation à metier
                    .exclude(formateurs__isnull=True)
                    .values_list('formateurs__id', flat=True)
                )
                
                requested_formateurs_pks = set(self.normalize_formateur_ids(formateur_ids))
                
                for pk in requested_formateurs_pks:
                    if pk not in allowed_formateur_ids_for_metier: # Changé allowed_formateur_ids_for_formation à allowed_formateur_ids_for_metier
                        formateur_obj = Formateur.objects.get(pk=pk)
                        errors.append(
                            f"Le formateur '{formateur_obj.nom} {formateur_obj.postnom}' ne dispense aucun module du métier sélectionné." # Changé formation à métier
                        )
            except Metier.DoesNotExist: # Changé Formation.DoesNotExist à Metier.DoesNotExist
                errors.append("Le métier sélectionné est introuvable.") # Changé formation à métier
        # --- Fin nouvelle logique ---

        return errors


@method_decorator(login_required, name="dispatch")
class ActionListViews(ActionPermissionMixin, ListView):
    context_object_name = "action_list"
    model = Action
    template_name = "progress/actions.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        actions = list(ctx["object_list"])

        for action in actions:
            action.status_meta = self.get_action_status(action)

        ctx["object_list"] = actions
        ctx["link"] = "actions"
        ctx["stats"] = {
            "total": len(actions),
            "planned": sum(1 for action in actions if action.status_meta["key"] == "planned"),
            "ongoing": sum(1 for action in actions if action.status_meta["key"] == "ongoing"),
            "completed": sum(1 for action in actions if action.status_meta["key"] == "completed"),
            "enrolled": sum(action.stagiaire_total for action in actions),
        }
        return ctx


@method_decorator(login_required, name="dispatch")
class ActionDetailViews(ActionPermissionMixin, DetailView):
    model = Action
    template_name = "progress/action_detail.html"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("detailaction_set__stagiaire", "formateurs")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        action = ctx["object"]
        inscriptions = action.detailaction_set.select_related("stagiaire").order_by("stagiaire__nom", "stagiaire__postnom")

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
        metier_id = request.POST["metier"] # Changé formation_id à metier_id
        formateur_ids = request.POST.getlist("formateurs")

        errors = self.validate_action_payload(date_debut, date_fin, metier_id, formateur_ids) # Changé formation_id à metier_id
        if errors:
            ctx = self.build_form_context(
                titre="Créer",
                mode="new",
                submitted=request.POST,
                selected_formateur_ids=self.normalize_formateur_ids(formateur_ids),
                form_errors=errors,
            )
            return render(request, "progress/action.html", ctx, status=400)

        action = Action(
            description=description,
            date_debut=date_debut,
            date_fin=date_fin,
            metier_id=metier_id, # Changé formation_id à metier_id
        )
        action.save()
        if formateur_ids:
            action.formateurs.set(Formateur.objects.filter(pk__in=self.normalize_formateur_ids(formateur_ids)))

        return HttpResponseRedirect(reverse_lazy("actions"))


@method_decorator(login_required, name="dispatch")
class ActionUpdateView(ActionPermissionMixin, UpdateView):
    model = Action
    template_name = "progress/action.html"
    fields = ["description", "date_debut", "date_fin", "metier"] # Changé formation à metier
    success_url = reverse_lazy("actions")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["metier"].queryset = self.get_allowed_metiers().select_related("filiere").order_by("nom") # Changé formation à metier
        return form

    def form_valid(self, form):
        formateur_ids = self.request.POST.getlist("formateurs")
        errors = self.validate_action_payload(
            form.cleaned_data["date_debut"],
            form.cleaned_data["date_fin"],
            str(form.cleaned_data["metier"].pk), # Changé formation à metier
            formateur_ids,
        )
        if errors:
            for error in errors:
                form.add_error(None, error)
            return self.form_invalid(form)
        response = super().form_valid(form)
        self.object.formateurs.set(Formateur.objects.filter(pk__in=self.normalize_formateur_ids(formateur_ids)))
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            self.build_form_context(
                titre="Modifier",
                mode="edit",
                selected_formateur_ids=self.normalize_formateur_ids(self.request.POST.getlist("formateurs")) if self.request.method == "POST" else list(self.object.formateurs.values_list("pk", flat=True)),
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