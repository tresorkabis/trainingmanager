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

from progress.models import Action
from training.models import Formation


class ActionPermissionMixin:
    def get_allowed_formations(self):
        user = self.request.user
        queryset = Formation.objects.all()

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
            .annotate(stagiaire_total=Count("detailaction"))
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
        context = {
            "formations": self.get_allowed_formations().select_related("filiere").order_by("nom"),
            "today": date.today(),
        }
        context.update(kwargs)
        return context

    def validate_action_payload(self, date_debut, date_fin, formation_id):
        errors = []
        allowed_formations = self.get_allowed_formations()

        if not allowed_formations.filter(pk=formation_id).exists():
            errors.append("La formation sélectionnée n'est pas autorisée pour votre périmètre.")
        if date_fin and date_debut and date_fin < date_debut:
            errors.append("La date de fin doit être postérieure ou égale à la date de début.")

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
        return super().get_queryset().prefetch_related("detailaction_set__stagiaire")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        action = ctx["object"]
        inscriptions = action.detailaction_set.select_related("stagiaire").order_by("stagiaire__nom", "stagiaire__postnom")

        ctx["status_meta"] = self.get_action_status(action)
        ctx["inscriptions"] = inscriptions
        ctx["link"] = "actions"
        ctx["inscription_count"] = inscriptions.count()
        return ctx


@method_decorator(login_required, name="dispatch")
class ActionCreateView(ActionPermissionMixin, View):
    def get(self, request):
        self.enforce_manage_permission()
        ctx = self.build_form_context(
            titre="Créer",
            mode="new",
            submitted={},
        )
        return render(request, "progress/action.html", ctx)

    def post(self, request):
        self.enforce_manage_permission()

        description = request.POST["description"].strip()
        date_debut = request.POST["date_debut"]
        date_fin = request.POST["date_fin"]
        formation_id = request.POST["formation"]

        errors = self.validate_action_payload(date_debut, date_fin, formation_id)
        if errors:
            ctx = self.build_form_context(
                titre="Créer",
                mode="new",
                submitted=request.POST,
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
        errors = self.validate_action_payload(
            form.cleaned_data["date_debut"],
            form.cleaned_data["date_fin"],
            str(form.cleaned_data["formation"].pk),
        )
        if errors:
            for error in errors:
                form.add_error(None, error)
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            self.build_form_context(
                titre="Modifier",
                mode="edit",
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
