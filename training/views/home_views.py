from django.shortcuts import render
from django.views.generic import View
from django.db.models import Count

from intern.models import Stagiaire
from progress.models import Action, DetailAction
from training.models import Filiere, Formation, Service
from users.models import User, Profile # Importation de Profile
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class HomeView(View):

    @method_decorator(login_required)
    def get(self, request):
        user = request.user 

        # Initialisation des querysets de base
        stagiaires_queryset = Stagiaire.objects.all()
        actions_queryset = Action.objects.all()
        metiers_queryset = Formation.objects.all()
        filieres_queryset = Filiere.objects.all()

        # Filtrage basé sur le rôle de l'utilisateur
        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            pass 
        elif user.profile and user.profile.name == "Chef de filière" and user.filiere:
            # Un chef de filière voit les données de sa filière
            # Filtrage des stagiaires par inscription (DetailAction)
            stagiaires_ids = DetailAction.objects.filter(
                action__formation__filiere=user.filiere
            ).values_list('stagiaire_id', flat=True).distinct()
            stagiaires_queryset = stagiaires_queryset.filter(id__in=stagiaires_ids)
            
            actions_queryset = actions_queryset.filter(formation__filiere=user.filiere)
            metiers_queryset = metiers_queryset.filter(filiere=user.filiere)
            filieres_queryset = filieres_queryset.filter(pk=user.filiere.pk)
            
        elif user.profile and user.profile.name == "Chef de service" and user.service:
            # Un chef de service voit les données des filières de son service
            stagiaires_ids = DetailAction.objects.filter(
                action__formation__filiere__service=user.service
            ).values_list('stagiaire_id', flat=True).distinct()
            stagiaires_queryset = stagiaires_queryset.filter(id__in=stagiaires_ids)
            
            actions_queryset = actions_queryset.filter(formation__filiere__service=user.service)
            metiers_queryset = metiers_queryset.filter(filiere__service=user.service)
            filieres_queryset = filieres_queryset.filter(service=user.service)
        else:
            stagiaires_queryset = Stagiaire.objects.none()
            actions_queryset = Action.objects.none()
            metiers_queryset = Formation.objects.none()
            filieres_queryset = Filiere.objects.none()


        # Calcul des statistiques par filière
        # Pour les stagiaires, on passe par DetailAction pour obtenir la filière
        stagiaire_counts_list = DetailAction.objects.filter(stagiaire__in=stagiaires_queryset).values(
            "action__formation__filiere__nom"
        ).annotate(total=Count("stagiaire", distinct=True))
        
        stagiaire_counts = {
            item["action__formation__filiere__nom"]: item["total"]
            for item in stagiaire_counts_list if item["action__formation__filiere__nom"]
        }

        action_counts = {
            item["formation__filiere__nom"]: item["total"]
            for item in actions_queryset.exclude(formation__filiere__nom__isnull=True)
            .values("formation__filiere__nom")
            .annotate(total=Count("id"))
        }

        filiere_names = set(stagiaire_counts.keys()) | set(action_counts.keys())
        filiere_totals = {
            name: stagiaire_counts.get(name, 0) + action_counts.get(name, 0)
            for name in filiere_names if name
        }
        
        sorted_filieres = sorted(
            filiere_totals.items(),
            key=lambda item: (-item[1], item[0]),
        )

        top_limit = 6
        top_filiere_names = [name for name, _ in sorted_filieres[:top_limit]]
        
        categories = top_filiere_names[:]
        stagiaire_data = [stagiaire_counts.get(name, 0) for name in top_filiere_names]
        action_data = [action_counts.get(name, 0) for name in top_filiere_names]

        if len(sorted_filieres) > top_limit:
            other_filieres = sorted_filieres[top_limit:]
            categories.append("Autres")
            stagiaire_data.append(sum(stagiaire_counts.get(name, 0) for name, _ in other_filieres))
            action_data.append(sum(action_counts.get(name, 0) for name, _ in other_filieres))

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
            "nbmetiers" : metiers_queryset.count(),
            "nbfilieres" : filieres_queryset.count(),
            "nbstagiaires" : stagiaires_queryset.count(),
            "nbactions" : actions_queryset.count(),
            "user" : user,
            "dashboard_chart": dashboard_chart,
        }
        return render(request, "home/index.html", ctx)
