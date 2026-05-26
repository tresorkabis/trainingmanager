from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import OuterRef, Subquery
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from intern.models import AutreFormation, Categorie, Entreprise, EtudeStagiaire, Stagiaire
from progress.models import DetailAction
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

    def enforce_create_permission(self):
        if not self.get_allowed_filieres().exists():
            raise PermissionDenied("Vous n'avez pas la permission de gérer les stagiaires.")


@method_decorator(login_required, name="dispatch")
class StagiaireListView(StagiairePermissionMixin, ListView):
    context_object_name = "stagiaire_list"
    paginate_by = 5
    template_name = "intern/stagiaires.html"

    def get_queryset(self):
        queryset = self.get_stagiaire_queryset().select_related("categorie", "entreprise", "filiere")

        latest_detail_action_pk = DetailAction.objects.filter(
            stagiaire=OuterRef("pk")
        ).order_by("-action__date_debut").values("pk")[:1]

        latest_formation_name = DetailAction.objects.filter(
            pk=Subquery(latest_detail_action_pk)
        ).values("action__formation__nom")[:1]

        return queryset.annotate(
            current_formation_name=Subquery(latest_formation_name, output_field=models.CharField())
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = "stagiaires"
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
        ).select_related("action__formation").order_by("action__date_debut")
        ctx["autres_formations"] = AutreFormation.objects.filter(stagiaire=current_stagiaire)
        ctx["titre"] = "Voir"
        return ctx


@method_decorator(login_required, name="dispatch")
class StagiaireCreateView(StagiairePermissionMixin, View):
    def get(self, request):
        self.enforce_create_permission()
        ctx = {
            "categories": Categorie.objects.all(),
            "entreprises": Entreprise.objects.all(),
            "filieres": self.get_allowed_filieres(),
            "titre": "Saisie d'un stagiaire",
            "mode": "new",
        }
        return render(request, "intern/stagiaire.html", ctx)

    def post(self, request):
        self.enforce_create_permission()

        nom = request.POST["nom"]
        postnom = request.POST["postnom"]
        prenom = request.POST["prenom"]
        adresse = request.POST["adresse"]
        sexe = request.POST["sexe"]
        telephone = request.POST["telephone"]
        email = request.POST.get("email") or None
        date_naissance = request.POST.get("date_naissance") or None
        lieu_naissance = request.POST.get("lieu_naissance") or None
        nationalite = request.POST.get("nationalite") or None
        type_piece = request.POST.get("type_piece") or None
        numero_piece = request.POST.get("numero_piece") or None
        nom_pere = request.POST.get("nom_pere") or None
        nom_mere = request.POST.get("nom_mere") or None
        niveau_etude = request.POST.get("niveau_etude") or None
        categorie_id = request.POST["categorie"]
        photo = request.FILES.get("photo")
        filiere_id = request.POST.get("filiere") or None

        categorie_obj = Categorie.objects.get(id=categorie_id)
        allowed_filieres = self.get_allowed_filieres()

        if filiere_id and not allowed_filieres.filter(pk=filiere_id).exists():
            raise PermissionDenied("Vous ne pouvez pas rattacher ce stagiaire à cette filière.")

        stagiaire = Stagiaire(
            nom=nom,
            postnom=postnom,
            prenom=prenom,
            adresse=adresse,
            sexe=sexe,
            telephone=telephone,
            email=email,
            date_naissance=date_naissance,
            lieu_naissance=lieu_naissance,
            nationalite=nationalite,
            type_piece=type_piece,
            numero_piece=numero_piece,
            nom_pere=nom_pere,
            nom_mere=nom_mere,
            niveau_etude=niveau_etude,
            photo=photo,
            categorie_id=categorie_id,
            filiere_id=filiere_id,
        )

        if categorie_obj.titre == "dans l'emploi":
            entreprise_id = request.POST.get("entreprise")
            stagiaire.entreprise_id = entreprise_id if entreprise_id else None
            stagiaire.fonction = request.POST.get("fonction") or None
            anciennete_emploi = request.POST.get("anciennete_emploi")
            stagiaire.anciennete_emploi = int(anciennete_emploi) if anciennete_emploi else None
            anciennete_entreprise = request.POST.get("anciennete_entreprise")
            stagiaire.anciennete_entreprise = int(anciennete_entreprise) if anciennete_entreprise else None
        else:
            stagiaire.entreprise = None
            stagiaire.fonction = None
            stagiaire.anciennete_emploi = None
            stagiaire.anciennete_entreprise = None

        stagiaire.save()

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

        return HttpResponseRedirect("/intern/stagiaires")
