from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models, transaction # Import transaction
from django.db.models import OuterRef, Subquery, Count
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


class StagiairePermissionMixin:
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

    def get_stagiaire_queryset(self):
        user = self.request.user
        queryset = Stagiaire.objects.all()

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(filiere=user.filiere)
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(filiere__service=user.service)
        return Stagiaire.objects.none()

    def enforce_manage_permission(self):
        user = self.request.user
        if not (user.is_superuser or (user.profile and user.profile.name == "Manager")):
            raise PermissionDenied("Vous n'avez pas la permission de gérer les stagiaires.")


@method_decorator(login_required, name="dispatch")
class StagiaireListView(StagiairePermissionMixin, ListView):
    context_object_name = "stagiaire_list"
    paginate_by = 6
    template_name = "intern/stagiaires.html"

    def get_queryset(self):
        self.enforce_manage_permission()
        queryset = self.get_stagiaire_queryset().select_related("categorie", "entreprise", "filiere")

        latest_detail_action_pk = DetailAction.objects.filter(
            stagiaire=OuterRef("pk")
        ).order_by("-action__date_debut").values("pk")[:1]

        latest_metier_name = DetailAction.objects.filter(
            pk=Subquery(latest_detail_action_pk)
        ).values("action__metier__nom")[:1]

        queryset = queryset.annotate(
            etudes_count=Count('etudes', distinct=True),
            autres_formations_count=Count('autres_formations', distinct=True)
        )

        return queryset.annotate(
            current_formation_name=Subquery(latest_metier_name, output_field=models.CharField())
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = "stagiaires"
        
        all_stagiaires = self.get_queryset()
        ctx['stats'] = {
            'total': all_stagiaires.count(),
            'dans_emploi': all_stagiaires.filter(categorie__titre="dans l'emploi").count(),
            'sans_emploi': all_stagiaires.filter(categorie__titre="sans emploi").count(),
            'non_defini': all_stagiaires.filter(categorie__titre="non défini").count(),
            'masculin': all_stagiaires.filter(sexe='M').count(),
            'feminin': all_stagiaires.filter(sexe='F').count(),
        }
        return ctx


@method_decorator(login_required, name="dispatch")
class StagiaireDetailView(StagiairePermissionMixin, DetailView):
    model = Stagiaire
    template_name = "intern/stagiaire.html"

    def get_queryset(self):
        return self.get_stagiaire_queryset().select_related("categorie", "entreprise", "filiere")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        current_stagiaire = self.get_object()

        ctx["stagiaires"] = self.get_stagiaire_queryset()
        ctx["categories"] = Categorie.objects.all()
        ctx["entreprises"] = Entreprise.objects.all()
        ctx["filieres"] = self.get_allowed_filieres()
        ctx["actions_suivies"] = DetailAction.objects.filter(
            stagiaire=current_stagiaire
        ).select_related("action__metier").order_by("action__date_debut")
        ctx["autres_formations"] = AutreFormation.objects.filter(stagiaire=current_stagiaire)
        ctx["paiements"] = Paiement.objects.filter(stagiaire=current_stagiaire).order_by('-date_paiement')
        ctx["titre"] = "Voir"
        ctx["mode"] = None  # Mode falsey pour activer le mode lecture dans le template
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
            "categories": Categorie.objects.all(), # Encore nécessaire pour le JS de l'onglet pro
            "entreprises": Entreprise.objects.all(), # Encore nécessaire pour le JS de l'onglet pro
            "filieres": self.get_allowed_filieres(),
            "actions": Action.objects.filter(active=True).select_related('metier'),
            "titre": titre,
            "mode": mode,
            "object": stagiaire,
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

                # Validation de la filière si elle est fournie
                if stagiaire.filiere and not self.get_allowed_filieres().filter(pk=stagiaire.filiere.pk).exists():
                    form.add_error('filiere', "Vous ne pouvez pas rattacher ce stagiaire à cette filière.")
                    return self.form_invalid(request, form, stagiaire, mode, titre)

                # Gérer les champs spécifiques à la catégorie "dans l'emploi"
                # La logique de clean_entreprise dans le form gère déjà la création de l'entreprise
                # Il faut juste s'assurer que les champs fonction, anciennete_emploi, anciennete_entreprise sont None si pas "dans l'emploi"
                if stagiaire.categorie and stagiaire.categorie.titre != "dans l'emploi":
                    stagiaire.entreprise = None
                    stagiaire.fonction = None
                    stagiaire.anciennete_emploi = None
                    stagiaire.anciennete_entreprise = None

                stagiaire.save()

                # Gérer les études et autres formations (logique existante)
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
            "categories": Categorie.objects.all(),
            "entreprises": Entreprise.objects.all(),
            "filieres": self.get_allowed_filieres(),
            "actions": Action.objects.filter(active=True).select_related('metier'),
            "titre": titre,
            "mode": mode,
            "object": stagiaire,
            "form_errors": form.errors, # Passer les erreurs du formulaire
        }
        # Reconstruire les études et autres formations pour repopuler le formulaire
        # Cette logique est nécessaire car nous n'utilisons pas de formsets pour ces éléments
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
        ctx["existing_studies"] = reconstructed_studies # Utiliser un nom différent pour éviter conflit avec object.etudes.all

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
        ctx["existing_other_trainings"] = reconstructed_other_trainings # Utiliser un nom différent

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
    qs = list_view.get_stagiaire_queryset().select_related('categorie', 'entreprise', 'filiere')

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