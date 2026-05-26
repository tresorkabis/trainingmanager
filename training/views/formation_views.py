from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from training.models import Filiere, Formation


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

    def enforce_create_permission(self):
        if not self.get_allowed_filieres().exists():
            raise PermissionDenied("Vous n'avez pas la permission de gérer les formations.")


@method_decorator(login_required, name="dispatch")
class FormationListView(FormationPermissionMixin, ListView):
    context_object_name = "formation_list"
    paginate_by = 4
    template_name = "training/formations.html"

    def get_queryset(self):
        return self.get_formation_queryset().select_related("filiere", "filiere__service")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = "formations"
        return ctx


@method_decorator(login_required, name="dispatch")
class FormationDetailView(FormationPermissionMixin, DetailView):
    model = Formation
    template_name = "training/formation.html"

    def get_queryset(self):
        return self.get_formation_queryset().select_related("filiere", "filiere__service")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filieres"] = self.get_allowed_filieres()
        ctx["titre"] = "Voir"
        return ctx


@method_decorator(login_required, name="dispatch")
class FormationCreateView(FormationPermissionMixin, View):
    def get(self, request):
        self.enforce_create_permission()
        ctx = {
            "filieres": self.get_allowed_filieres(),
            "titre": "Saisie d'une formation",
            "mode": "new",
        }
        return render(request, "training/formation.html", ctx)

    def post(self, request):
        self.enforce_create_permission()

        nom = request.POST["nom"]
        duree = request.POST["duree"]
        duree_heures = request.POST.get("duree_heures") or 0
        filiere_id = request.POST["filiere"]
        cout = request.POST.get("cout") or 0
        frais_participation = request.POST.get("frais_participation") or 0
        frais_jury = request.POST.get("frais_jury") or 0
        frais_materiels = request.POST.get("frais_materiels") or 0

        if not self.get_allowed_filieres().filter(pk=filiere_id).exists():
            raise PermissionDenied("Vous ne pouvez pas rattacher cette formation à cette filière.")

        formation = Formation(
            nom=nom,
            duree=duree,
            duree_heures=duree_heures,
            filiere_id=filiere_id,
            cout=cout,
            frais_participation=frais_participation,
            frais_jury=frais_jury,
            frais_materiels=frais_materiels,
        )
        formation.save()

        return HttpResponseRedirect("/training/formations")
