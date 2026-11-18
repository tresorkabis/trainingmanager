from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from intern.models import Entreprise
from intern.forms import EntrepriseForm


class EntrepriseManagerMixin:
    def enforce_manager_permission(self):
        user = self.request.user
        if not (user.is_superuser or (user.profile and user.profile.name == "Manager")):
            raise PermissionDenied("Vous n'avez pas la permission de gérer les entreprises.")


@method_decorator(login_required, name="dispatch")
class EntrepriseListView(EntrepriseManagerMixin, ListView):
    model = Entreprise
    context_object_name = "entreprise_list"
    template_name = "intern/entreprises.html"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        self.enforce_manager_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Entreprise.objects.annotate(stagiaires_count=Count("stagiaire", distinct=True))
            .order_by("nom")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["link"] = "entreprises"
        context["titre"] = "Entreprises"
        context["total_entreprises"] = self.get_queryset().count()
        context["hero_actions"] = [
            {"label": "Ajouter une entreprise", "url": reverse_lazy("entreprise_create"), "icon": "bi bi-plus-circle"},
        ]
        return context


@method_decorator(login_required, name="dispatch")
class EntrepriseDetailView(EntrepriseManagerMixin, DetailView):
    model = Entreprise
    context_object_name = "entreprise"
    template_name = "intern/entreprise_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.enforce_manager_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Entreprise.objects.prefetch_related("stagiaire_set__categorie").annotate(
            stagiaires_count=Count("stagiaire", distinct=True)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["link"] = "entreprises"
        context["titre"] = self.object.nom
        context["stagiaires"] = self.object.stagiaire_set.order_by("nom", "postnom", "prenom")
        context["hero_stats"] = [
            {"label": "Stagiaires associés", "value": self.object.stagiaires_count},
            {"label": "Statut", "value": "Active" if self.object.active else "Inactive"},
        ]
        context["hero_actions"] = [
            {"label": "Retour aux entreprises", "url": "/intern/entreprises", "icon": "bi bi-arrow-left", "class": "btn-light-secondary"},
            {"label": "Modifier", "url": reverse_lazy("entreprise_update", kwargs={"pk": self.object.pk}), "icon": "bi bi-pencil"},
        ]
        return context


@method_decorator(login_required, name="dispatch")
class EntrepriseCreateView(EntrepriseManagerMixin, CreateView):
    model = Entreprise
    form_class = EntrepriseForm
    template_name = "intern/entreprise_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.enforce_manager_permission()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "L'entreprise a été créée.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("entreprise", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "titre": "Ajouter une entreprise",
            "link": "entreprises",
            "hero_actions": [{"label": "Retour aux entreprises", "url": reverse_lazy("entreprises"), "icon": "bi bi-arrow-left", "class": "btn-light-secondary"}],
        })
        return context


@method_decorator(login_required, name="dispatch")
class EntrepriseUpdateView(EntrepriseManagerMixin, UpdateView):
    model = Entreprise
    form_class = EntrepriseForm
    template_name = "intern/entreprise_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.enforce_manager_permission()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Les informations de l'entreprise ont été modifiées.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("entreprise", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "titre": "Modifier une entreprise",
            "link": "entreprises",
            "hero_actions": [{"label": "Retour à l’entreprise", "url": reverse_lazy("entreprise", kwargs={"pk": self.object.pk}), "icon": "bi bi-arrow-left", "class": "btn-light-secondary"}],
        })
        return context
