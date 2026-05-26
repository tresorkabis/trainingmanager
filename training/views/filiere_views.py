from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from training.models import Filiere, Service


class FilierePermissionMixin:
    def get_filiere_queryset(self):
        user = self.request.user
        queryset = Filiere.objects.all()

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(pk=user.filiere.pk)
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(service=user.service)
        return Filiere.objects.none()

    def get_allowed_services(self):
        user = self.request.user
        queryset = Service.objects.all()

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(pk=user.service.pk)
        return Service.objects.none()

    def enforce_create_permission(self):
        if not self.get_allowed_services().exists():
            raise PermissionDenied("Vous n'avez pas la permission de gérer les filières.")


@method_decorator(login_required, name="dispatch")
class FiliereListView(FilierePermissionMixin, ListView):
    context_object_name = "filiere_list"
    paginate_by = 4
    template_name = "training/filieres.html"

    def get_queryset(self):
        return self.get_filiere_queryset().select_related("service")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = "filieres"
        return ctx


@method_decorator(login_required, name="dispatch")
class FiliereDetailView(FilierePermissionMixin, DetailView):
    model = Filiere
    template_name = "training/filiere.html"

    def get_queryset(self):
        return self.get_filiere_queryset().select_related("service")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["services"] = self.get_allowed_services()
        ctx["titre"] = "Voir"
        return ctx


@method_decorator(login_required, name="dispatch")
class FiliereCreateView(FilierePermissionMixin, View):
    def get(self, request):
        self.enforce_create_permission()
        ctx = {
            "services": self.get_allowed_services(),
        }
        return render(request, "training/filiere.html", ctx)

    def post(self, request):
        self.enforce_create_permission()

        nom = request.POST["nom"]
        service_id = request.POST["service"]

        if not self.get_allowed_services().filter(pk=service_id).exists():
            raise PermissionDenied("Vous ne pouvez pas rattacher cette filière à ce service.")

        filiere = Filiere(
            nom=nom,
            service_id=service_id,
        )
        filiere.save()

        return HttpResponseRedirect("/training/filieres")
