from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models, transaction # Import transaction
from django.db.models import OuterRef, Subquery, Count, Sum # Import Sum for aggregation
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView, DeleteView

from intern.models import AutreFormation, Categorie, Entreprise, EtudeStagiaire, Stagiaire
from intern.forms import StagiaireForm # Import StagiaireForm
from progress.models import DetailAction, Paiement, Action
from training.models import Filiere

ALLOWED_CATEGORIE_TITRES = ["dans l'emploi", "sans emploi"]


class StagiairePermissionMixin:
    def get_action_status(self, action):
        today = date.today()
        if action.date_fin < today:
            return {"label": "Terminée", "badge": "bg-light-secondary text-dark", "key": "completed"}
        if action.date_debut > today:
            return {"label": "Planifiée", "badge": "bg-light-primary text-primary", "key": "planned"}
        return {"label": "En cours", "badge": "bg-light-success text-success", "key": "ongoing"}

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

    def get_allowed_categories(self):
        return Categorie.objects.filter(titre__in=ALLOWED_CATEGORIE_TITRES).order_by("titre")

    def get_stagiaire_queryset(self):
        user = self.request.user
        queryset = Stagiaire.objects.all()

        if user.is_superuser or (user.profile and user.profile.name in ["Manager", "Conseiller"]):
            return queryset
        
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            # Filtrer les stagiaires inscrits à des actions dont la formation est dans la filière de l'utilisateur
            detail_actions_in_filiere = DetailAction.objects.filter(
                action__formation__filiere=user.filiere
            ).values_list('stagiaire__pk', flat=True)
            return queryset.filter(pk__in=detail_actions_in_filiere).distinct()

        if user.profile and user.profile.name == "Chef de service" and user.service:
            # Filtrer les stagiaires inscrits à des actions dont la formation est dans un service de l'utilisateur
            detail_actions_in_service = DetailAction.objects.filter(
                action__formation__filiere__service=user.service
            ).values_list('stagiaire__pk', flat=True)
            return queryset.filter(pk__in=detail_actions_in_service).distinct()
        
        return Stagiaire.objects.none()


    def enforce_manage_permission(self):
        user = self.request.user
        allowed_profiles = ["Manager", "Conseiller"]
        if not (user.is_superuser or (user.profile and user.profile.name in allowed_profiles)):
            raise PermissionDenied("Vous n'avez pas la permission de gérer les stagiaires.")


@method_decorator(login_required, name="dispatch")
class StagiaireListView(StagiairePermissionMixin, ListView):
    context_object_name = "stagiaire_list"
    paginate_by = 6
    template_name = "intern/stagiaires.html"

    def get_queryset(self):
        self.enforce_manage_permission()
        # Suppression de 'filiere' de select_related
        queryset = self.get_stagiaire_queryset().select_related("categorie", "entreprise")

        from django.utils import timezone
        from django.db.models.functions import Coalesce

        today = timezone.now().date()

        latest_detail_action_pk = DetailAction.objects.filter(
            stagiaire=OuterRef("pk")
        ).order_by("-action__date_debut").values("pk")[:1]

        active_detail_action_pk = DetailAction.objects.filter(
            stagiaire=OuterRef("pk"),
            action__date_debut__lte=today,
            action__date_fin__gte=today
        ).order_by("-action__date_debut").values("pk")[:1]

        active_formation_name = DetailAction.objects.filter(
            pk=Subquery(active_detail_action_pk)
        ).values("action__formation__nom")[:1]

        latest_formation_name = DetailAction.objects.filter(
            pk=Subquery(latest_detail_action_pk)
        ).values("action__formation__nom")[:1]

        queryset = queryset.annotate(
            etudes_count=Count('etudes', distinct=True),
            autres_formations_count=Count('autres_formations', distinct=True)
        )

        return queryset.annotate(
            current_formation_name=Coalesce(
                Subquery(active_formation_name, output_field=models.CharField()),
                Subquery(latest_formation_name, output_field=models.CharField())
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = "stagiaires"
        
        all_stagiaires = self.get_queryset()
        total = all_stagiaires.count()
        dans_emploi = all_stagiaires.filter(categorie__titre="dans l'emploi").count()
        sans_emploi = all_stagiaires.filter(categorie__titre="sans emploi").count()
        masculin = all_stagiaires.filter(sexe='M').count()
        feminin = all_stagiaires.filter(sexe='F').count()

        ctx['stats'] = {
            'total': total,
            'dans_emploi': dans_emploi,
            'sans_emploi': sans_emploi,
            'masculin': masculin,
            'feminin': feminin,
        }

        ctx["hero_stats"] = [
            {'label': 'Total Stagiaires', 'value': total},
            {'label': "Dans l'emploi", 'value': dans_emploi},
            {'label': 'Sans emploi', 'value': sans_emploi},
            {'label': 'Féminin', 'value': feminin},
        ]

        ctx["hero_actions"] = [
            {'label': 'Nouveau stagiaire', 'url': reverse_lazy('stagiaire_create'), 'icon': 'bi bi-person-plus'},
            {'label': 'Imprimer', 'url': reverse_lazy('stagiaires_print'), 'icon': 'bi bi-printer', 'class': 'btn-light-secondary'},
        ]

        return ctx


@method_decorator(login_required, name="dispatch")
class StagiaireDetailView(StagiairePermissionMixin, DetailView): # Correction de la faute de frappe ici
    model = Stagiaire
    template_name = "intern/stagiaire.html"

    def get_queryset(self):
        return (
            self.get_stagiaire_queryset()
            .select_related("categorie", "entreprise")
            .prefetch_related("etudes", "autres_formations", "paiements")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        current_stagiaire = self.get_object()
        
        # Calcul des informations de paiement
        total_paid = current_stagiaire.paiements.aggregate(total=Sum('montant'))['total'] or 0
        
        formations_cost_qs = DetailAction.objects.filter(
            stagiaire=current_stagiaire
        ).values_list('action__formation__cout', flat=True).distinct()
        
        total_cost = sum(formations_cost_qs) if formations_cost_qs else 0
        solde_restant = total_cost - total_paid

        actions_suivies = list(
            DetailAction.objects.filter(stagiaire=current_stagiaire)
            .select_related("action__formation")
            .order_by("action__date_debut")
        )
        action_ids_inscrits = [da.action_id for da in actions_suivies]
        for detail_action in actions_suivies:
            detail_action.status_meta = self.get_action_status(detail_action.action)

        ctx["total_cost"] = total_cost
        ctx["total_paid"] = total_paid
        ctx["solde_restant"] = solde_restant

        ctx["hero_stats"] = [
            {'label': 'Montant Facturé', 'value': f"{total_cost:,.0f} USD"},
            {'label': 'Versements', 'value': f"{total_paid:,.0f} USD"},
            {'label': 'Solde restant', 'value': f"{solde_restant:,.0f} USD"},
            {'label': 'Inscriptions', 'value': len(actions_suivies)},
        ]
        ctx["photo_url"] = current_stagiaire.photo.url if current_stagiaire.photo else None

        ctx["hero_actions"] = [
            {'label': 'Retour', 'url': reverse_lazy('stagiaires'), 'icon': 'bi bi-arrow-left', 'class': 'btn-light-secondary'},
            {'label': 'Modifier', 'url': reverse_lazy('stagiaire_update', kwargs={'pk': current_stagiaire.pk}), 'icon': 'bi bi-pencil'},
        ]

        ctx["stagiaires"] = self.get_stagiaire_queryset()
        ctx["categories"] = self.get_allowed_categories()
        ctx["entreprises"] = Entreprise.objects.all()
        ctx["filieres"] = self.get_allowed_filieres() # Conserver pour la permission mixin si nécessaire
        ctx["actions_suivies"] = actions_suivies
        ctx["actions_disponibles"] = Action.objects.filter(active=True).select_related("formation", "formation__filiere").exclude(pk__in=action_ids_inscrits).order_by("-date_debut", "description")
        ctx["autres_formations"] = AutreFormation.objects.filter(stagiaire=current_stagiaire)
        ctx["paiements"] = Paiement.objects.filter(stagiaire=current_stagiaire).order_by('-date_paiement')
        ctx["titre"] = "Voir"
        ctx["mode"] = None
        return ctx


@method_decorator(login_required, name="dispatch")
class StagiaireCreateUpdateView(StagiairePermissionMixin, View):
    template_name = "intern/stagiaire.html"

    def get(self, request, pk=None):
        self.enforce_manage_permission()
        stagiaire = None
        if pk:
            stagiaire = get_object_or_404(Stagiaire, pk=pk)
            form = StagiaireForm(instance=stagiaire)
            mode = "edit"
            titre = "Modifier un stagiaire"
        else:
            form = StagiaireForm()
            mode = "new"
            titre = "Saisie d'un stagiaire"

        ctx = {
            "form": form,
            "categories": self.get_allowed_categories(),
            "entreprises": Entreprise.objects.all(),
            "filieres": self.get_allowed_filieres(), # Conserver pour la permission mixin si nécessaire
            "actions": Action.objects.filter(active=True).select_related("formation"),
            "titre": titre,
            "mode": mode,
            "object": stagiaire,
            "hero_actions": [
                {'label': 'Retour', 'url': reverse_lazy('stagiaires'), 'icon': 'bi bi-arrow-left', 'class': 'btn-light-secondary'},
            ],
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        self.enforce_manage_permission()
        stagiaire = None
        if pk:
            stagiaire = get_object_or_404(Stagiaire, pk=pk)
            form = StagiaireForm(request.POST, request.FILES, instance=stagiaire)
            mode = "edit"
            titre = "Modifier un stagiaire"
        else:
            form = StagiaireForm(request.POST, request.FILES)
            mode = "new"
            titre = "Saisie d'un stagiaire"

        if form.is_valid():
            with transaction.atomic():
                stagiaire = form.save(commit=False)

                if stagiaire.categorie and stagiaire.categorie.titre != "dans l'emploi":
                    stagiaire.entreprise = None
                    stagiaire.fonction = None
                    stagiaire.anciennete_emploi = None
                    stagiaire.anciennete_entreprise = None

                stagiaire.save()

                EtudeStagiaire.objects.filter(stagiaire=stagiaire).delete()
                etude_intitules = request.POST.getlist("etude_intitule[]")
                etude_etablissements = request.POST.getlist("etude_etablissement[]")
                etude_niveaux = request.POST.getlist("etude_niveau[]")
                etude_annee_debuts = request.POST.getlist("etude_annee_debut[]")
                etude_annee_fins = request.POST.getlist("etude_annee_fin[]")
                etude_diplomes = request.POST.getlist("etude_diplome[]")

                for index, intitule in enumerate(etude_intitules):
                    intitule = (intitule or "").strip()
                    if not intitule:
                        continue

                    annee_debut = etude_annee_debuts[index].strip() if index < len(etude_annee_debuts) else ""
                    annee_fin = etude_annee_fins[index].strip() if index < len(etude_annee_fins) else ""

                    EtudeStagiaire.objects.create(
                        stagiaire=stagiaire,
                        intitule=intitule,
                        etablissement=etude_etablissements[index].strip() if index < len(etude_etablissements) else None,
                        niveau=etude_niveaux[index].strip() if index < len(etude_niveaux) else None,
                        annee_debut=int(annee_debut) if annee_debut else None,
                        annee_fin=int(annee_fin) if annee_fin else None,
                        diplome_obtenu=etude_diplomes[index].strip() if index < len(etude_diplomes) else None,
                    )

                AutreFormation.objects.filter(stagiaire=stagiaire).delete()
                autre_formation_intitules = request.POST.getlist("autre_formation_intitule[]")
                autre_formation_etablissements = request.POST.getlist("autre_formation_etablissement[]")
                autre_formation_annee_fins = request.POST.getlist("autre_formation_annee_fin[]")

                for index, intitule in enumerate(autre_formation_intitules):
                    intitule = (intitule or "").strip()
                    if not intitule:
                        continue

                    annee_fin = autre_formation_annee_fins[index].strip() if index < len(autre_formation_annee_fins) else ""

                    AutreFormation.objects.create(
                        stagiaire=stagiaire,
                        intitule=intitule,
                        etablissement=autre_formation_etablissements[index].strip() if index < len(autre_formation_etablissements) else None,
                        annee_fin=int(annee_fin) if annee_fin else None,
                    )

            messages.success(request, f"Le stagiaire '{stagiaire.get_full_name()}' a été {'mis à jour' if pk else 'créé'} avec succès.")
            return HttpResponseRedirect(reverse_lazy("stagiaire", kwargs={'pk': stagiaire.pk}))
        else:
            return self.form_invalid(request, form, stagiaire, mode, titre)

    def form_invalid(self, request, form, stagiaire, mode, titre):
        ctx = {
            "form": form,
            "categories": self.get_allowed_categories(),
            "entreprises": Entreprise.objects.all(),
            "filieres": self.get_allowed_filieres(), # Conserver pour la permission mixin si nécessaire
            "actions": Action.objects.filter(active=True).select_related("formation"),
            "titre": titre,
            "mode": mode,
            "object": stagiaire,
            "form_errors": form.errors,
            "hero_actions": [
                {'label': 'Retour', 'url': reverse_lazy('stagiaires'), 'icon': 'bi bi-arrow-left', 'class': 'btn-light-secondary'},
            ],
        }
        reconstructed_studies = []
        etude_intitules = request.POST.getlist("etude_intitule[]")
        etude_etablissements = request.POST.getlist("etude_etablissement[]")
        etude_niveaux = request.POST.getlist("etude_niveau[]")
        etude_annee_debuts = request.POST.getlist("etude_annee_debut[]")
        etude_annee_fins = request.POST.getlist("etude_annee_fin[]")
        etude_diplomes = request.POST.getlist("etude_diplome[]")

        for index, intitule in enumerate(etude_intitules):
            if intitule.strip():
                reconstructed_studies.append({
                    'intitule': intitule,
                    'etablissement': etude_etablissements[index] if index < len(etude_etablissements) else '',
                    'niveau': etude_niveaux[index] if index < len(etude_niveaux) else '',
                    'annee_debut': etude_annee_debuts[index] if index < len(etude_annee_debuts) else '',
                    'annee_fin': etude_annee_fins[index] if index < len(etude_annee_fins) else '',
                    'diplome_obtenu': etude_diplomes[index] if index < len(etude_diplomes) else '',
                })
        ctx["existing_studies"] = reconstructed_studies

        reconstructed_other_trainings = []
        autre_formation_intitules = request.POST.getlist("autre_formation_intitule[]")
        autre_formation_etablissements = request.POST.getlist("autre_formation_etablissement[]")
        autre_formation_annee_fins = request.POST.getlist("autre_formation_annee_fin[]")

        for index, intitule in enumerate(autre_formation_intitules):
            if intitule.strip():
                reconstructed_other_trainings.append({
                    'intitule': intitule,
                    'etablissement': autre_formation_etablissements[index] if index < len(autre_formation_etablissements) else '',
                    'annee_fin': autre_formation_annee_fins[index] if index < len(autre_formation_annee_fins) else '',
                })
        ctx["existing_other_trainings"] = reconstructed_other_trainings

        return render(request, self.template_name, ctx, status=400)


@method_decorator(login_required, name="dispatch")
class StagiaireDeleteView(DeleteView):
    model = Stagiaire
    template_name = "intern/stagiaire_confirm_delete.html"
    success_url = reverse_lazy("stagiaires")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        return ctx


# Print cards view
from django.core.paginator import Paginator

@login_required
def stagiaire_cards_print(request):
    # reuse list view helpers by creating an instance and binding request
    list_view = StagiaireListView()
    list_view.request = request
    # Use the ListView.get_queryset() to preserve the annotations (current_formation_name)
    # Suppression de 'filiere' de select_related
    qs = list_view.get_queryset().select_related('categorie', 'entreprise')

    # Optional: filter by selected ids (ids=1,2,3)
    ids = request.GET.get('ids')
    if ids:
        try:
            id_list = [int(x) for x in ids.split(',') if x.strip().isdigit()]
            qs = qs.filter(pk__in=id_list)
        except Exception:
            pass

    # Support printing a specific page: ?page=1
    page = request.GET.get('page')
    try:
        page_num = int(page) if page else 1
    except Exception:
        page_num = 1

    paginator = Paginator(qs, list_view.paginate_by or 20)
    page_obj = paginator.get_page(page_num)
    ctx = {
        'object_list': page_obj.object_list,
    }
    return render(request, 'intern/stagiaire_cards_print.html', ctx)
