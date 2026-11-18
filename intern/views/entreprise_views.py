from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from intern.models import Entreprise


@method_decorator(login_required, name="dispatch")
class EntrepriseListView(ListView):
    model = Entreprise
    context_object_name = "entreprise_list"
    template_name = "intern/entreprises.html"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_superuser or (user.profile and user.profile.name == "Manager")):
            raise PermissionDenied("Vous n'avez pas la permission de consulter les entreprises.")
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
        return context


@method_decorator(login_required, name="dispatch")
class EntrepriseDetailView(DetailView):
    model = Entreprise
    context_object_name = "entreprise"
    template_name = "intern/entreprise_detail.html"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_superuser or (user.profile and user.profile.name == "Manager")):
            raise PermissionDenied("Vous n'avez pas la permission de consulter les entreprises.")
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
        ]
        return context
