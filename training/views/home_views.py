from django.shortcuts import render
from django.views.generic import View
from django.db.models import Count

from intern.models import Stagiaire
from progress.models import Action
from training.models import Filiere, Formation, Service
from users.models import User, Profile # Importation de Profile
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class HomeView(View):

    @method_decorator(login_required)
    def get(self, request):
        user = request.user # L'utilisateur est déjà disponible via request.user

        # Initialisation des querysets de base
        stagiaires_queryset = Stagiaire.objects.all()
        actions_queryset = Action.objects.all()
        metiers_queryset = Formation.objects.all() # Changé formations_queryset à metiers_queryset
        filieres_queryset = Filiere.objects.all()

        # Filtrage basé sur le rôle de l'utilisateur
        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            # Les superutilisateurs et les managers voient toutes les données
            pass # Pas de filtrage supplémentaire nécessaire
        elif user.profile and user.profile.name == "Chef de filière" and user.filiere:
            # Un chef de filière voit les données de sa filière
            stagiaires_queryset = stagiaires_queryset.filter(filiere=user.filiere)
            actions_queryset = actions_queryset.filter(formation__filiere=user.filiere)
            metiers_queryset = metiers_queryset.filter(filiere=user.filiere) # Changé formations_queryset à metiers_queryset
            filieres_queryset = filieres_queryset.filter(pk=user.filiere.pk) # Ne voit que sa propre filière
        elif user.profile and user.profile.name == "Chef de service" and user.service:
            # Un chef de service voit les données des filières de son service
            stagiaires_queryset = stagiaires_queryset.filter(filiere__service=user.service)
            actions_queryset = actions_queryset.filter(formation__filiere__service=user.service)
            metiers_queryset = metiers_queryset.filter(filiere__service=user.service) # Changé formations_queryset à metiers_queryset
            filieres_queryset = filieres_queryset.filter(service=user.service)
        else:
            # Pour les autres profils (ex: "User") ou si pas de lien, ne voient aucune donnée
            stagiaires_queryset = Stagiaire.objects.none()
            actions_queryset = Action.objects.none()
            metiers_queryset = Formation.objects.none() # Changé formations_queryset à metiers_queryset
            filieres_queryset = Filiere.objects.none()


        # Calcul des statistiques basées sur les querysets filtrés
        stagiaire_counts = {
            item["filiere__nom"]: item["total"]
            for item in stagiaires_queryset.exclude(filiere__nom__isnull=True)
            .values("filiere__nom")
            .annotate(total=Count("id"))
        }
        action_counts = {
            item["formation__filiere__nom"]: item["total"] # Changé formation__filiere__nom à metier__filiere__nom
            for item in actions_queryset.exclude(formation__filiere__nom__isnull=True) # Changé formation__filiere__nom à metier__filiere__nom
            .values("formation__filiere__nom") # Changé formation__filiere__nom à metier__filiere__nom
            .annotate(total=Count("id"))
        }

        filiere_totals = {
            name: stagiaire_counts.get(name, 0) + action_counts.get(name, 0)
            for name in set(stagiaire_counts.keys()) | set(action_counts.keys())
        }
        sorted_filieres = sorted(
            filiere_totals.items(),
            key=lambda item: (-item[1], item[0]),
        )

        top_limit = 6
        top_filiere_names = [name for name, _ in sorted_filieres[:top_limit]]
        other_names = [name for name, _ in sorted_filieres[top_limit:]]

        categories = top_filiere_names[:]
        stagiaire_data = [stagiaire_counts.get(name, 0) for name in top_filiere_names]
        action_data = [action_counts.get(name, 0) for name in top_filiere_names]

        if other_names:
            categories.append("Autres")
            stagiaire_data.append(sum(stagiaire_counts.get(name, 0) for name in other_names))
            action_data.append(sum(action_counts.get(name, 0) for name in other_names))

        dashboard_chart = {
            "title": "Répartition par filière",
            "categories": categories,
            "series": [
                {
                    "name": "Stagiaires",
                    "data": stagiaire_data,
                },
                {
                    "name": "Actions",
                    "data": action_data,
                },
            ],
        }

        ctx = {
            "link":"home",
            "nbmetiers" : metiers_queryset.count(), # Changé nbformations à nbmetiers
            "nbfilieres" : filieres_queryset.count(),
            "nbstagiaires" : stagiaires_queryset.count(),
            "nbactions" : actions_queryset.count(),
            "user" : user,
            "dashboard_chart": dashboard_chart,
        }
        return render(request, "home/index.html", ctx)
