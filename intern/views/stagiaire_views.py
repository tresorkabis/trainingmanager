from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import OuterRef, Subquery, Count # Import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView, DeleteView # Import UpdateView and DeleteView

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

    def enforce_manage_permission(self): # Renommé pour être plus générique
        user = self.request.user
        if not (user.is_superuser or (user.profile and user.profile.name == "Manager")):
            raise PermissionDenied("Vous n'avez pas la permission de gérer les stagiaires.")


@method_decorator(login_required, name="dispatch")
class StagiaireListView(StagiairePermissionMixin, ListView):
    context_object_name = "stagiaire_list"
    paginate_by = 5
    template_name = "intern/stagiaires.html"

    def get_queryset(self):
        self.enforce_manage_permission() # Vérifier la permission avant de construire le queryset
        queryset = self.get_stagiaire_queryset().select_related("categorie", "entreprise", "filiere")

        latest_detail_action_pk = DetailAction.objects.filter(
            stagiaire=OuterRef("pk")
        ).order_by("-action__date_debut").values("pk")[:1]

        latest_metier_name = DetailAction.objects.filter( # Changé latest_formation_name à latest_metier_name
            pk=Subquery(latest_detail_action_pk)
        ).values("action__metier__nom")[:1] # Changé action__formation__nom à action__metier__nom

        # Annoter chaque stagiaire avec le nombre d'études et d'autres formations
        queryset = queryset.annotate(
            etudes_count=Count('etudes', distinct=True),
            autres_formations_count=Count('autres_formations', distinct=True)
        )

        return queryset.annotate(
            current_formation_name=Subquery(latest_metier_name, output_field=models.CharField()) # Changé latest_formation_name à latest_metier_name
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = "stagiaires"
        
        # Calcul des statistiques globales
        all_stagiaires = self.get_queryset() # Utiliser le queryset annoté
        ctx['stats'] = {
            'total': all_stagiaires.count(),
            'dans_emploi': all_stagiaires.filter(categorie__titre="dans l'emploi").count(),
            'sans_emploi': all_stagiaires.filter(categorie__titre="sans emploi").count(),
            'non_defini': all_stagiaires.filter(categorie__titre="non défini").count(),
            'masculin': all_stagiaires.filter(sexe='M').count(), # Nouvelle stat
            'feminin': all_stagiaires.filter(sexe='F').count(),   # Nouvelle stat
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
        ).select_related("action__metier").order_by("action__date_debut") # Changé action__formation à action__metier
        ctx["autres_formations"] = AutreFormation.objects.filter(stagiaire=current_stagiaire)
        ctx["titre"] = "Voir"
        return ctx


@method_decorator(login_required, name="dispatch")
class StagiaireCreateUpdateView(StagiairePermissionMixin, View): # Nouvelle vue pour créer/modifier
    template_name = "intern/stagiaire.html" # Utilise le même template que le détail pour l'instant

    def get(self, request, pk=None):
        self.enforce_manage_permission()
        stagiaire = None
        if pk:
            stagiaire = get_object_or_404(Stagiaire, pk=pk)
        
        ctx = {
            "categories": Categorie.objects.all(),
            "entreprises": Entreprise.objects.all(),
            "filieres": self.get_allowed_filieres(),
            "titre": "Modifier un stagiaire" if pk else "Saisie d'un stagiaire",
            "mode": "edit" if pk else "new",
            "object": stagiaire,
            "submitted": {}, # Pour gérer les erreurs de formulaire
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        self.enforce_manage_permission()
        stagiaire = None
        if pk:
            stagiaire = get_object_or_404(Stagiaire, pk=pk)

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

        errors = []
        if not nom: errors.append("Le nom est requis.")
        if not postnom: errors.append("Le postnom est requis.")
        if not prenom: errors.append("Le prénom est requis.")
        if not adresse: errors.append("L'adresse est requise.")
        if not sexe: errors.append("Le sexe est requis.")
        if not telephone: errors.append("Le téléphone est requis.")
        if not email: errors.append("L'email est requis.")
        if not categorie_id: errors.append("La catégorie est requise.")

        if filiere_id and not allowed_filieres.filter(pk=filiere_id).exists():
            errors.append("Vous ne pouvez pas rattacher ce stagiaire à cette filière.")
        
        # Validation d'unicité de l'email
        if email and Stagiaire.objects.filter(email=email).exclude(pk=pk).exists():
            errors.append(f"Un stagiaire avec l'email '{email}' existe déjà.")
        # Validation d'unicité du numéro de pièce
        if numero_piece and Stagiaire.objects.filter(numero_piece=numero_piece).exclude(pk=pk).exists():
            errors.append(f"Un stagiaire avec le numéro de pièce '{numero_piece}' existe déjà.")


        if errors:
            ctx = {
                "categories": Categorie.objects.all(),
                "entreprises": Entreprise.objects.all(),
                "filieres": self.get_allowed_filieres(),
                "titre": "Modifier un stagiaire" if pk else "Saisie d'un stagiaire",
                "mode": "edit" if pk else "new",
                "object": stagiaire, # Si c'est une modification, l'objet existe
                "submitted": request.POST, # Repopuler le formulaire avec les données soumises
                "form_errors": errors,
            }
            return render(request, self.template_name, ctx, status=400)


        if stagiaire: # Mode édition
            stagiaire.nom = nom
            stagiaire.postnom = postnom
            stagiaire.prenom = prenom
            stagiaire.adresse = adresse
            stagiaire.sexe = sexe
            stagiaire.telephone = telephone
            stagiaire.email = email
            stagiaire.date_naissance = date_naissance
            stagiaire.lieu_naissance = lieu_naissance
            stagiaire.nationalite = nationalite
            stagiaire.type_piece = type_piece
            stagiaire.numero_piece = numero_piece
            stagiaire.nom_pere = nom_pere
            stagiaire.nom_mere = nom_mere
            stagiaire.niveau_etude = niveau_etude
            stagiaire.categorie_id = categorie_id
            stagiaire.filiere_id = filiere_id
            if photo: stagiaire.photo = photo
            
            # Gérer les champs spécifiques à la catégorie "dans l'emploi"
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

        else: # Mode création
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
            # Gérer les champs spécifiques à la catégorie "dans l'emploi"
            if categorie_obj.titre == "dans l'emploi":
                entreprise_id = request.POST.get("entreprise")
                stagiaire.entreprise_id = entreprise_id if entreprise_id else None
                stagiaire.fonction = request.POST.get("fonction") or None
                anciennete_emploi = request.POST.get("anciennete_emploi")
                stagiaire.anciennete_emploi = int(anciennete_emploi) if anciennete_emploi else None
                anciennete_entreprise = request.POST.get("anciennete_entreprise")
                stagiaire.anciennete_entreprise = int(anciennete_entreprise) if anciennete_entreprise else None
            
            stagiaire.save()

        # Gérer les études et autres formations (simplifié pour l'exemple, à adapter pour update)
        # Pour l'update, il faudrait comparer les existants avec les soumis et faire des create/update/delete
        EtudeStagiaire.objects.filter(stagiaire=stagiaire).delete() # Supprime tout et recrée
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

        return HttpResponseRedirect(reverse_lazy("stagiaire", kwargs={'pk': stagiaire.pk})) # Rediriger vers le détail du stagiaire


@method_decorator(login_required, name="dispatch")
class StagiaireDeleteView(DeleteView): # StagiairePermissionMixin est déjà dans la classe parente
    model = Stagiaire
    template_name = "intern/stagiaire_confirm_delete.html" # Nouveau template pour la confirmation de suppression
    success_url = reverse_lazy("stagiaires")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        return ctx