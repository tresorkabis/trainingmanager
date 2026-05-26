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
        formations_queryset = Formation.objects.all()
        filieres_queryset = Filiere.objects.all()

        # Filtrage basé sur le rôle de l'utilisateur
        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            # Les superutilisateurs et les managers voient toutes les données
            pass # Pas de filtrage supplémentaire nécessaire
        elif user.profile and user.profile.name == "Chef de filière" and user.filiere:
            # Un chef de filière voit les données de sa filière
            stagiaires_queryset = stagiaires_queryset.filter(filiere=user.filiere)
            actions_queryset = actions_queryset.filter(formation__filiere=user.filiere)
            formations_queryset = formations_queryset.filter(filiere=user.filiere)
            filieres_queryset = filieres_queryset.filter(pk=user.filiere.pk) # Ne voit que sa propre filière
        elif user.profile and user.profile.name == "Chef de service" and user.service:
            # Un chef de service voit les données des filières de son service
            stagiaires_queryset = stagiaires_queryset.filter(filiere__service=user.service)
            actions_queryset = actions_queryset.filter(formation__filiere__service=user.service)
            formations_queryset = formations_queryset.filter(filiere__service=user.service)
            filieres_queryset = filieres_queryset.filter(service=user.service)
        else:
            # Pour les autres profils (ex: "User") ou si pas de lien, ne voient aucune donnée
            stagiaires_queryset = Stagiaire.objects.none()
            actions_queryset = Action.objects.none()
            formations_queryset = Formation.objects.none()
            filieres_queryset = Filiere.objects.none()


        # Calcul des statistiques basées sur les querysets filtrés
        stagiaire_counts = {
            item["filiere__nom"]: item["total"]
            for item in stagiaires_queryset.exclude(filiere__nom__isnull=True)
            .values("filiere__nom")
            .annotate(total=Count("id"))
        }
        action_counts = {
            item["formation__filiere__nom"]: item["total"]
            for item in actions_queryset.exclude(formation__filiere__nom__isnull=True)
            .values("formation__filiere__nom")
            .annotate(total=Count("id"))
        }

        filiere_categories = sorted(
            set(stagiaire_counts.keys()) | set(action_counts.keys()),
            key=lambda name: (-(stagiaire_counts.get(name, 0) + action_counts.get(name, 0)), name),
        )

        dashboard_chart = {
            "categories": filiere_categories,
            "series": [
                {
                    "name": "Stagiaires",
                    "data": [stagiaire_counts.get(name, 0) for name in filiere_categories],
                },
                {
                    "name": "Actions planifiées",
                    "data": [action_counts.get(name, 0) for name in filiere_categories],
                },
            ],
        }

        ctx = {
            "link":"home",
            "nbformations" : formations_queryset.count(),
            "nbfilieres" : filieres_queryset.count(),
            "nbstagiaires" : stagiaires_queryset.count(),
            "nbactions" : actions_queryset.count(),
            "user" : user,
            "dashboard_chart": dashboard_chart,
        }
        return render(request, "home/index.html", ctx)