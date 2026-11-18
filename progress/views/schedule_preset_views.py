from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView, View
from django.urls import reverse_lazy

from progress.models import Action, SchedulePreset
from progress.services import ActionWorkflowService


class SchedulePresetPermissionMixin:
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        allowed = user.is_superuser or (
            getattr(getattr(user, "profile", None), "name", None)
            in ActionPermissionProfiles
        )
        if not allowed:
            raise PermissionDenied("Vous n'avez pas la permission de gérer les configurations de créneaux.")
        return super().dispatch(request, *args, **kwargs)


ActionPermissionProfiles = {"Manager", "Chef de filière", "Chef de service"}


@method_decorator(login_required, name="dispatch")
class SchedulePresetListView(SchedulePresetPermissionMixin, ListView):
    model = SchedulePreset
    template_name = "progress/schedule_presets.html"
    context_object_name = "presets"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["link"] = "schedule_presets"
        context["titre"] = "Configurations des créneaux"
        context["hero_actions"] = [
            {"label": "Retour aux actions", "url": reverse_lazy("actions"), "icon": "bi bi-arrow-left", "class": "btn-light-secondary"},
        ]
        context["hero_stats"] = [{"label": "Configurations", "value": self.get_queryset().count()}]
        context["days"] = Action.DAY_OF_WEEK_CHOICES
        return context


@method_decorator(login_required, name="dispatch")
class SchedulePresetCreateView(SchedulePresetPermissionMixin, View):
    def post(self, request, *args, **kwargs):
        name = request.POST.get("name", "").strip()
        schedules = ActionWorkflowService.extract_action_schedules(request.POST)
        errors = ActionWorkflowService.validate_action_schedules(schedules)
        if not name:
            errors.insert(0, "Le nom de la configuration est requis.")
        if SchedulePreset.objects.filter(name__iexact=name).exists():
            errors.insert(0, "Une configuration porte déjà ce nom.")
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect("schedule_presets")

        try:
            with transaction.atomic():
                SchedulePreset.objects.create(
                    name=name,
                    schedules=[
                        {
                            "jour_semaine": int(item["jour_semaine"]),
                            "heure_debut": item["heure_debut"],
                            "heure_fin": item["heure_fin"],
                        }
                        for item in schedules
                    ],
                )
        except IntegrityError:
            messages.error(request, "Une configuration porte déjà ce nom.")
        else:
            messages.success(request, f"La configuration « {name} » a été créée.")
        return redirect("schedule_presets")


@method_decorator(login_required, name="dispatch")
class SchedulePresetDeleteView(SchedulePresetPermissionMixin, View):
    def post(self, request, pk, *args, **kwargs):
        preset = SchedulePreset.objects.filter(pk=pk).first()
        if preset:
            name = preset.name
            preset.delete()
            messages.success(request, f"La configuration « {name} » a été supprimée.")
        return redirect("schedule_presets")
